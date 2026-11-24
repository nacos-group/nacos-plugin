/*
 * Copyright 1999-2026 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.alibaba.nacos.plugin.ai.importer.skillhub;

import com.alibaba.nacos.api.exception.NacosException;
import com.alibaba.nacos.api.exception.api.NacosApiException;
import com.alibaba.nacos.api.model.v2.ErrorCode;
import com.alibaba.nacos.common.utils.JacksonUtils;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.AiResourceImportConstants;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportArtifact;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportCandidate;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportCandidatePage;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportContext;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportItem;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportPayloadKind;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;
import com.alibaba.nacos.plugin.ai.importer.skillhub.http.DefaultSkillHubHttpClient;
import com.alibaba.nacos.plugin.ai.importer.skillhub.http.SkillHubHttpClient;
import com.alibaba.nacos.plugin.ai.importer.skillhub.http.SkillHubHttpResponse;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportService;
import com.fasterxml.jackson.databind.JsonNode;

import java.io.ByteArrayInputStream;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Importer for SkillHub registry APIs (Nacos 3.2.x SPI).
 *
 * @author nacos
 */
public class SkillHubImportService implements AiResourceImportService {
    
    public static final String RESOURCE_TYPE_SKILL = AiResourceImportConstants.RESOURCE_TYPE_SKILL;
    
    private static final String METADATA_SOURCE = "source";
    
    private static final String METADATA_NAMESPACE = "namespace";
    
    private static final String METADATA_SKILL_ID = "skillId";
    
    private static final String METADATA_VERSION = "version";
    
    private static final String METADATA_CANONICAL_SLUG = "canonicalSlug";
    
    private static final String METADATA_CHECKSUM = "checksum";
    
    private static final String OPTION_NAMESPACE = "namespace";
    
    private static final String DEFAULT_NAMESPACE = "global";
    
    private static final String SKILL_MARKDOWN_FILE = "SKILL.md";
    
    private static final int DEFAULT_LIMIT = 100;
    
    private static final String SOURCE_VALUE = "skillhub";
    
    private final SkillHubHttpClient httpClient;
    
    public SkillHubImportService() {
        this(new DefaultSkillHubHttpClient());
    }
    
    SkillHubImportService(SkillHubHttpClient httpClient) {
        this.httpClient = httpClient;
    }
    
    @Override
    public String importerType() {
        return SkillHubImportServiceBuilder.IMPORTER_TYPE;
    }
    
    @Override
    public Set<String> supportedResourceTypes() {
        return Collections.singleton(RESOURCE_TYPE_SKILL);
    }
    
    @Override
    public AiResourceImportCandidatePage search(AiResourceImportContext context) throws NacosException {
        try {
            SkillHubImportConfig config = resolveConfig(context);
            SkillHubSlug.NamespaceQuery namespaceQuery = resolveSearchNamespaceQuery(context, config);
            String apiRoot = resolveApiRoot(config);
            int resultLimit = resolveLimit(context.getLimit(), config);
            List<SkillHubRemoteSkill> skills = listPublishedSkills(config, apiRoot,
                    namespaceQuery.getNamespace(), resultLimit);
            List<AiResourceImportCandidate> candidates = toCandidates(namespaceQuery.getNamespace(),
                    skills, namespaceQuery.getKeyword(), resultLimit);
            AiResourceImportCandidatePage result = new AiResourceImportCandidatePage();
            result.setItems(candidates);
            result.setHasMore(false);
            result.setNextCursor(null);
            return result;
        } catch (NacosException e) {
            throw e;
        } catch (Exception e) {
            throw dataAccess("Search SkillHub source failed: " + e.getMessage(), e);
        }
    }
    
    @Override
    public AiResourceImportArtifact fetch(AiResourceImportContext context, AiResourceImportItem item)
            throws NacosException {
        try {
            SkillHubImportConfig config = resolveConfig(context);
            String apiRoot = resolveApiRoot(config);
            SkillHubRemoteSkill skill = resolveSkillRef(context, config, item);
            byte[] zipBytes = downloadZip(config, apiRoot, skill);
            checkDownloadedSize(config, zipBytes.length);
            validateSkillZip(zipBytes);
            AiResourceImportArtifact result = new AiResourceImportArtifact();
            result.setResourceType(RESOURCE_TYPE_SKILL);
            result.setExternalId(skill.getCanonicalSlug());
            result.setName(skill.getLocalName());
            result.setPayloadKind(AiResourceImportPayloadKind.SKILL_ZIP);
            result.setPayload(zipBytes);
            String checksum = sha256Hex(zipBytes);
            result.setChecksum(checksum);
            result.setSourceMetadata(buildArtifactMetadata(skill, checksum));
            return result;
        } catch (NacosException e) {
            throw e;
        } catch (Exception e) {
            throw dataAccess("Fetch SkillHub artifact failed: " + e.getMessage(), e);
        }
    }
    
    private SkillHubImportConfig resolveConfig(AiResourceImportContext context) throws NacosException {
        AiResourceImportSource source = requireSource(context);
        SkillHubImportConfig config = new SkillHubImportConfig(source);
        if (StringUtils.isBlank(config.getEndpoint())) {
            throw invalid("SkillHub import source endpoint must not be empty.");
        }
        if (StringUtils.isBlank(config.getToken())) {
            throw invalid("SkillHub import source token must not be empty.");
        }
        return config;
    }
    
    /**
     * Resolve namespace for search: options.namespace &gt; {@code @ns} query &gt; config default &gt; global.
     */
    private SkillHubSlug.NamespaceQuery resolveSearchNamespaceQuery(AiResourceImportContext context,
            SkillHubImportConfig config) throws NacosException {
        String optionNamespace = optionValue(context, OPTION_NAMESPACE);
        String defaultNamespace = StringUtils.isNotBlank(config.getNamespace())
                ? config.getNamespace() : DEFAULT_NAMESPACE;
        SkillHubSlug.NamespaceQuery parsed =
                SkillHubSlug.parseSearchQuery(context.getQuery(), defaultNamespace);
        String namespace = StringUtils.isNotBlank(optionNamespace)
                ? SkillHubSlug.normalizeNamespace(optionNamespace) : parsed.getNamespace();
        if (StringUtils.isBlank(namespace)) {
            namespace = DEFAULT_NAMESPACE;
        }
        String keyword = StringUtils.isNotBlank(optionNamespace) ? nullToEmpty(context.getQuery()).trim()
                : parsed.getKeyword();
        if (StringUtils.isNotBlank(optionNamespace) && keyword.startsWith("@")) {
            // options already selected ns; strip a redundant @prefix from free-text query.
            SkillHubSlug.NamespaceQuery again = SkillHubSlug.parseSearchQuery(keyword, namespace);
            keyword = again.getKeyword();
            if (StringUtils.isNotBlank(again.getNamespace())) {
                namespace = again.getNamespace();
            }
        }
        return new SkillHubSlug.NamespaceQuery(namespace, keyword);
    }
    
    private AiResourceImportSource requireSource(AiResourceImportContext context) throws NacosException {
        if (context == null || context.getSource() == null) {
            throw invalid("SkillHub import source must not be null.");
        }
        return context.getSource();
    }
    
    private List<SkillHubRemoteSkill> listPublishedSkills(SkillHubImportConfig config, String apiRoot,
            String namespace, int limit) throws Exception {
        String ns = SkillHubSlug.normalizeNamespace(namespace);
        List<ListStrategy> strategies = new ArrayList<ListStrategy>();
        strategies.add(new ListStrategy(apiRoot + "/api/v1/skills",
                "namespaceSlug=" + encodeQueryValue(ns) + "&page=0&size=" + limit + "&limit=" + limit));
        strategies.add(new ListStrategy(apiRoot + "/api/v1/skills",
                "namespace=" + encodeQueryValue(ns) + "&page=0&size=" + limit + "&limit=" + limit));
        strategies.add(new ListStrategy(apiRoot + "/api/web/skills",
                "namespace=" + encodeQueryValue(ns) + "&q=&page=0&size=" + limit));
        strategies.add(new ListStrategy(apiRoot + "/api/v1/search",
                "q=" + encodeQueryValue("@" + ns) + "&page=1&limit=" + limit));
        if ("global".equals(ns)) {
            strategies.add(0, new ListStrategy(apiRoot + "/api/v1/search",
                    "q=&page=1&limit=" + limit));
        }
        
        int authFailures = 0;
        int attempts = 0;
        Map<String, SkillHubRemoteSkill> byName = new LinkedHashMap<String, SkillHubRemoteSkill>();
        for (ListStrategy strategy : strategies) {
            attempts++;
            String url = strategy.path + "?" + strategy.query;
            SkillHubHttpResponse response = httpClient.get(config, url, true, null, true);
            int status = response.getStatusCode();
            if (status == 401 || status == 403) {
                authFailures++;
                continue;
            }
            if (!response.isSuccess()) {
                continue;
            }
            List<SkillHubRemoteSkill> parsed = parseSkillList(ns, response.getBody());
            for (SkillHubRemoteSkill skill : parsed) {
                byName.put(skill.getLocalName(), skill);
            }
            if (!byName.isEmpty()) {
                return new ArrayList<SkillHubRemoteSkill>(byName.values());
            }
        }
        if (byName.isEmpty() && authFailures == attempts && attempts > 0) {
            throw invalid("SkillHub list authentication failed for namespace: " + ns);
        }
        return new ArrayList<SkillHubRemoteSkill>(byName.values());
    }
    
    private List<SkillHubRemoteSkill> parseSkillList(String namespace, byte[] body) throws Exception {
        if (body == null || body.length == 0) {
            return Collections.emptyList();
        }
        JsonNode root = JacksonUtils.toObj(new String(body, StandardCharsets.UTF_8), JsonNode.class);
        List<JsonNode> items = extractItemList(root);
        List<SkillHubRemoteSkill> result = new ArrayList<SkillHubRemoteSkill>();
        for (JsonNode item : items) {
            if (item == null || !item.isObject()) {
                continue;
            }
            SkillHubRemoteSkill parsed = parseRemoteSkill(namespace, item);
            if (parsed != null) {
                result.add(parsed);
            }
        }
        return result;
    }
    
    private List<JsonNode> extractItemList(JsonNode root) {
        if (root == null || root.isNull()) {
            return Collections.emptyList();
        }
        if (root.isArray()) {
            List<JsonNode> result = new ArrayList<JsonNode>();
            for (JsonNode each : root) {
                result.add(each);
            }
            return result;
        }
        if (!root.isObject()) {
            return Collections.emptyList();
        }
        for (String key : new String[] {"results", "items", "content", "records", "list"}) {
            JsonNode val = root.get(key);
            if (val != null && val.isArray()) {
                List<JsonNode> result = new ArrayList<JsonNode>();
                for (JsonNode each : val) {
                    result.add(each);
                }
                return result;
            }
        }
        JsonNode data = root.get("data");
        if (data != null && data.isArray()) {
            List<JsonNode> result = new ArrayList<JsonNode>();
            for (JsonNode each : data) {
                result.add(each);
            }
            return result;
        }
        if (data != null && data.isObject()) {
            for (String key : new String[] {"results", "items", "content", "records", "list"}) {
                JsonNode val = data.get(key);
                if (val != null && val.isArray()) {
                    List<JsonNode> result = new ArrayList<JsonNode>();
                    for (JsonNode each : val) {
                        result.add(each);
                    }
                    return result;
                }
            }
        }
        return Collections.emptyList();
    }
    
    private SkillHubRemoteSkill parseRemoteSkill(String namespace, JsonNode item) {
        String rawSlug = firstText(item, "slug", "skillSlug", "name");
        if (StringUtils.isBlank(rawSlug)) {
            return null;
        }
        String explicitNsRaw = firstText(item, "namespace", "namespaceSlug");
        String explicitNs = StringUtils.isBlank(explicitNsRaw) ? ""
                : SkillHubSlug.normalizeNamespace(explicitNsRaw);
        String canonical;
        String localName;
        if (rawSlug.contains("--")) {
            canonical = rawSlug;
            if (!SkillHubSlug.skillBelongsToNamespace(namespace, canonical)) {
                return null;
            }
            try {
                localName = SkillHubSlug.localSkillNameFromCanonical(namespace, canonical);
            } catch (IllegalArgumentException e) {
                return null;
            }
        } else {
            if (StringUtils.isNotBlank(explicitNs)) {
                if (!explicitNs.equals(namespace)) {
                    return null;
                }
            } else if (!"global".equals(namespace)) {
                return null;
            }
            localName = rawSlug;
            canonical = SkillHubSlug.hubCanonicalSlug(namespace, localName);
        }
        String version = extractVersion(item);
        if (StringUtils.isBlank(version)) {
            return null;
        }
        String description = textOrEmpty(item.get("description"));
        return new SkillHubRemoteSkill(canonical, localName, version, description);
    }
    
    private String extractVersion(JsonNode item) {
        JsonNode published = item.get("publishedVersion");
        if (published != null && published.isObject()) {
            String version = textOrEmpty(published.get("version"));
            if (StringUtils.isNotBlank(version)) {
                return version;
            }
        } else if (published != null && published.isTextual()) {
            String version = published.asText().trim();
            if (StringUtils.isNotBlank(version)) {
                return version;
            }
        }
        for (String key : new String[] {"latestVersion", "latest_version"}) {
            JsonNode latest = item.get(key);
            if (latest != null && latest.isObject()) {
                String version = textOrEmpty(latest.get("version"));
                if (StringUtils.isNotBlank(version)) {
                    return version;
                }
            } else if (latest != null && latest.isTextual()) {
                String version = latest.asText().trim();
                if (StringUtils.isNotBlank(version)) {
                    return version;
                }
            }
        }
        return textOrEmpty(item.get("version"));
    }
    
    private List<AiResourceImportCandidate> toCandidates(String namespace,
            List<SkillHubRemoteSkill> skills, String query, int limit) {
        if (skills == null || skills.isEmpty()) {
            return Collections.emptyList();
        }
        String normalizedQuery = query == null ? "" : query.trim().toLowerCase(Locale.ENGLISH);
        List<AiResourceImportCandidate> result = new ArrayList<AiResourceImportCandidate>();
        for (SkillHubRemoteSkill skill : skills) {
            if (skill == null) {
                continue;
            }
            if (StringUtils.isNotBlank(normalizedQuery) && !matchesQuery(skill, normalizedQuery)) {
                continue;
            }
            AiResourceImportCandidate candidate = new AiResourceImportCandidate();
            candidate.setResourceType(RESOURCE_TYPE_SKILL);
            candidate.setExternalId(skill.getCanonicalSlug());
            candidate.setName(skill.getLocalName());
            // Console matches validate results by `${externalId}__${version}`; keep in sync.
            candidate.setVersion(skill.getVersion());
            candidate.setDescription(skill.getDescription());
            candidate.setMetadata(buildCandidateMetadata(namespace, skill));
            result.add(candidate);
            if (result.size() >= limit) {
                break;
            }
        }
        return result;
    }
    
    private boolean matchesQuery(SkillHubRemoteSkill skill, String normalizedQuery) {
        return containsIgnoreCase(skill.getLocalName(), normalizedQuery)
                || containsIgnoreCase(skill.getDescription(), normalizedQuery)
                || containsIgnoreCase(skill.getCanonicalSlug(), normalizedQuery);
    }
    
    private boolean containsIgnoreCase(String value, String needle) {
        if (StringUtils.isBlank(value)) {
            return false;
        }
        return value.toLowerCase(Locale.ENGLISH).contains(needle);
    }
    
    private SkillHubRemoteSkill resolveSkillRef(AiResourceImportContext context,
            SkillHubImportConfig config, AiResourceImportItem item) throws NacosException {
        if (item == null) {
            throw invalid("SkillHub import item must not be null.");
        }
        Map<String, String> metadata = item.getMetadata();
        String namespace = metadata == null ? null : metadata.get(METADATA_NAMESPACE);
        if (StringUtils.isBlank(namespace)) {
            namespace = optionValue(context, OPTION_NAMESPACE);
        }
        if (StringUtils.isBlank(namespace)) {
            namespace = config.getNamespace();
        }
        String version = metadata == null ? null : metadata.get(METADATA_VERSION);
        String canonical = metadata == null ? null : metadata.get(METADATA_CANONICAL_SLUG);
        String skillId = metadata == null ? null : metadata.get(METADATA_SKILL_ID);
        if (StringUtils.isBlank(canonical)) {
            canonical = StringUtils.isNotBlank(item.getExternalId()) ? item.getExternalId() : item.getName();
        }
        if (StringUtils.isBlank(canonical)) {
            throw invalid("SkillHub import item must include canonical slug or external id.");
        }
        if (StringUtils.isBlank(namespace) && canonical.contains("--")) {
            namespace = SkillHubSlug.normalizeNamespace(canonical.split("--", 2)[0]);
        }
        if (StringUtils.isBlank(namespace)) {
            namespace = "global";
        } else {
            namespace = SkillHubSlug.normalizeNamespace(namespace);
        }
        if (StringUtils.isBlank(skillId)) {
            try {
                skillId = SkillHubSlug.localSkillNameFromCanonical(namespace, canonical);
            } catch (IllegalArgumentException e) {
                skillId = item.getName();
            }
        }
        if (StringUtils.isBlank(version)) {
            throw invalid("SkillHub import item must include version metadata.");
        }
        if (StringUtils.isBlank(skillId)) {
            skillId = canonical;
        }
        // Keep canonical consistent with the resolved namespace for non-global skills.
        if (!"global".equals(namespace) && !canonical.contains("--")) {
            canonical = SkillHubSlug.hubCanonicalSlug(namespace, skillId);
        }
        return new SkillHubRemoteSkill(canonical.trim(), skillId.trim(), version.trim(), "",
                namespace);
    }
    
    private byte[] downloadZip(SkillHubImportConfig config, String apiRoot, SkillHubRemoteSkill skill)
            throws Exception {
        List<String> urls = buildDownloadUrls(apiRoot, skill);
        Exception lastError = null;
        for (String url : urls) {
            try {
                return fetchZipFollowingRedirects(config, apiRoot, url, null, true, 0);
            } catch (Exception e) {
                lastError = e;
            }
        }
        if (lastError instanceof NacosException) {
            throw (NacosException) lastError;
        }
        if (lastError != null) {
            throw dataAccess("SkillHub download failed: " + lastError.getMessage(), lastError);
        }
        throw invalid("SkillHub download failed for " + skill.getCanonicalSlug());
    }
    
    /**
     * Build download URL candidates for iflytek/skillhub.
     *
     * <p>Primary routes are {@code GET /api/v1/skills/{ns}/{slug}/[versions/{ver}/]download}.
     * ClawHub-compatible fallbacks use {@code GET /api/v1/download/{canonicalSlug}?version=}
     * (and the query form), which redirect to the skills download path.
     */
    private List<String> buildDownloadUrls(String apiRoot, SkillHubRemoteSkill skill) throws Exception {
        String slug = skill.getCanonicalSlug();
        String version = skill.getVersion();
        String namespace;
        String shortName;
        if (slug.contains("--")) {
            String[] parts = slug.split("--", 2);
            namespace = parts[0];
            shortName = parts[1];
        } else {
            namespace = StringUtils.isNotBlank(skill.getNamespace()) ? skill.getNamespace() : "global";
            shortName = slug;
        }
        String nsSeg = encodePathSegment(namespace);
        String nameSeg = encodePathSegment(shortName);
        String versionSeg = encodePathSegment(version);
        String canonicalSeg = encodePathSegment(slug);
        String versionQuery = encodeQueryValue(version);
        
        List<String> urls = new ArrayList<String>();
        // Prefer the concrete versioned package first.
        urls.add(apiRoot + "/api/v1/skills/" + nsSeg + "/" + nameSeg + "/versions/" + versionSeg
                + "/download");
        urls.add(apiRoot + "/api/v1/skills/" + nsSeg + "/" + nameSeg + "/download");
        // ClawHub-compatible download entrypoints (302 -> skills download path).
        urls.add(apiRoot + "/api/v1/download/" + canonicalSeg + "?version=" + versionQuery);
        urls.add(apiRoot + "/api/v1/download?slug=" + encodeQueryValue(slug) + "&version="
                + versionQuery);
        return urls;
    }
    
    private byte[] fetchZipFollowingRedirects(SkillHubImportConfig config, String apiRoot, String url,
            String hostHeader, boolean withAuth, int depth) throws Exception {
        if (depth > 5) {
            throw new IllegalStateException("SkillHub download redirect limit exceeded for " + url);
        }
        SkillHubHttpResponse response = httpClient.get(config, url, false, hostHeader, withAuth);
        if (response.isRedirect()) {
            String location = response.getLocation();
            if (StringUtils.isBlank(location)) {
                throw new IllegalStateException(
                        "HTTP " + response.getStatusCode() + " without Location for " + url);
            }
            URI absolute = URI.create(url).resolve(location.trim());
            RedirectRewrite rewrite = rewriteRedirectLocation(config, absolute.toString());
            boolean nextWithAuth = isSkillHubApiUrl(apiRoot, rewrite.getFetchUrl());
            return fetchZipFollowingRedirects(config, apiRoot, rewrite.getFetchUrl(),
                    rewrite.getHostHeader(), nextWithAuth, depth + 1);
        }
        if (!response.isSuccess()) {
            throw new IllegalStateException(
                    "HTTP " + response.getStatusCode() + " when fetching " + url);
        }
        byte[] zip = zipBytesFromResponse(response.getBody());
        if (zip == null) {
            throw new IllegalStateException("SkillHub download response is not a zip: " + url);
        }
        return zip;
    }
    
    private boolean isSkillHubApiUrl(String apiRoot, String fetchUrl) {
        if (StringUtils.isBlank(fetchUrl)) {
            return false;
        }
        try {
            URI api = URI.create(apiRoot);
            URI target = URI.create(fetchUrl);
            if (StringUtils.isBlank(target.getHost())) {
                return true;
            }
            if (StringUtils.isBlank(api.getHost()) || !api.getHost().equalsIgnoreCase(target.getHost())) {
                return false;
            }
            int apiPort = api.getPort() >= 0 ? api.getPort() : defaultPort(api.getScheme());
            int targetPort = target.getPort() >= 0 ? target.getPort() : defaultPort(target.getScheme());
            if (apiPort != targetPort) {
                return false;
            }
            String path = target.getPath() == null ? "" : target.getPath();
            return path.startsWith("/api/");
        } catch (IllegalArgumentException e) {
            return false;
        }
    }
    
    private int defaultPort(String scheme) {
        if ("https".equalsIgnoreCase(scheme)) {
            return 443;
        }
        if ("http".equalsIgnoreCase(scheme)) {
            return 80;
        }
        return -1;
    }
    
    RedirectRewrite rewriteRedirectLocation(SkillHubImportConfig config, String location)
            throws NacosException {
        if (StringUtils.isBlank(location)) {
            return new RedirectRewrite(location, null);
        }
        URI parsed;
        try {
            parsed = URI.create(location.trim());
        } catch (IllegalArgumentException e) {
            return new RedirectRewrite(location, null);
        }
        String hostname = parsed.getHost();
        if (StringUtils.isBlank(hostname)) {
            return new RedirectRewrite(location, null);
        }
        Map<String, String> mapping = config.getRedirectHostMap();
        String target = mapping.get(hostname);
        if (target == null && "minio".equals(hostname)) {
            URI apiBase = URI.create(trimTrailingSlash(config.getEndpoint()));
            if (StringUtils.isNotBlank(apiBase.getHost())) {
                target = apiBase.getHost();
            }
        }
        if (StringUtils.isBlank(target) || target.equals(hostname)) {
            return new RedirectRewrite(location, null);
        }
        String originalNetloc = parsed.getPort() >= 0 ? hostname + ":" + parsed.getPort() : hostname;
        String newNetloc = parsed.getPort() >= 0 ? target + ":" + parsed.getPort() : target;
        try {
            String newUrl = new URI(parsed.getScheme(), newNetloc, parsed.getPath(), parsed.getQuery(),
                    parsed.getFragment()).toString();
            return new RedirectRewrite(newUrl, originalNetloc);
        } catch (java.net.URISyntaxException e) {
            return new RedirectRewrite(location, null);
        }
    }
    
    private byte[] zipBytesFromResponse(byte[] body) {
        if (body == null || body.length < 2) {
            return null;
        }
        if (body[0] == 'P' && body[1] == 'K') {
            return body;
        }
        if (body[0] != '{' && body[0] != '[') {
            return body;
        }
        return null;
    }
    
    private void validateSkillZip(byte[] zipBytes) throws Exception {
        boolean hasSkillMarkdown = false;
        try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(zipBytes),
                StandardCharsets.UTF_8)) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (entry.isDirectory()) {
                    continue;
                }
                String name = normalizeZipEntryName(entry.getName());
                if (StringUtils.isBlank(name)) {
                    continue;
                }
                validatePathSafety(name);
                String fileName = name.contains("/") ? name.substring(name.lastIndexOf('/') + 1) : name;
                if (SKILL_MARKDOWN_FILE.equalsIgnoreCase(fileName)) {
                    hasSkillMarkdown = true;
                }
            }
        }
        if (!hasSkillMarkdown) {
            throw invalid("SkillHub zip must contain SKILL.md.");
        }
    }
    
    private String normalizeZipEntryName(String path) {
        if (StringUtils.isBlank(path)) {
            return null;
        }
        String result = path.trim().replace('\\', '/');
        while (result.startsWith("./")) {
            result = result.substring(2);
        }
        return result;
    }
    
    private void validatePathSafety(String path) throws NacosException {
        if (StringUtils.isBlank(path) || path.startsWith("/") || path.contains("\\")) {
            throw invalid("SkillHub zip path is invalid: " + path);
        }
        String[] segments = path.split("/");
        for (String segment : segments) {
            if (StringUtils.isBlank(segment) || ".".equals(segment) || "..".equals(segment)) {
                throw invalid("SkillHub zip path is invalid: " + path);
            }
        }
    }
    
    private void checkDownloadedSize(SkillHubImportConfig config, long totalSize) throws NacosException {
        if (config.getMaxArtifactSize() > 0 && totalSize > config.getMaxArtifactSize()) {
            throw invalid("SkillHub artifact size exceeds source limit.");
        }
    }
    
    private Map<String, String> buildCandidateMetadata(String namespace, SkillHubRemoteSkill skill) {
        Map<String, String> metadata = new LinkedHashMap<String, String>();
        metadata.put(METADATA_SOURCE, SOURCE_VALUE);
        metadata.put(METADATA_NAMESPACE, namespace);
        metadata.put(METADATA_SKILL_ID, skill.getLocalName());
        metadata.put(METADATA_VERSION, skill.getVersion());
        metadata.put(METADATA_CANONICAL_SLUG, skill.getCanonicalSlug());
        return metadata;
    }
    
    private Map<String, String> buildArtifactMetadata(SkillHubRemoteSkill skill, String checksum) {
        Map<String, String> metadata = buildCandidateMetadata(
                StringUtils.isBlank(skill.getNamespace()) ? "global" : skill.getNamespace(), skill);
        if (StringUtils.isNotBlank(checksum)) {
            metadata.put(METADATA_CHECKSUM, checksum);
        }
        return metadata;
    }
    
    private String optionValue(AiResourceImportContext context, String key) {
        if (context == null || context.getOptions() == null || StringUtils.isBlank(key)) {
            return null;
        }
        return context.getOptions().get(key);
    }
    
    private int resolveLimit(int limit, SkillHubImportConfig config) {
        if (limit <= 0) {
            return Math.min(DEFAULT_LIMIT, config.getMaxItemCount());
        }
        return Math.min(limit, config.getMaxItemCount());
    }
    
    private String resolveApiRoot(SkillHubImportConfig config) throws NacosException {
        return trimTrailingSlash(config.getEndpoint());
    }
    
    private String encodePathSegment(String value) throws UnsupportedEncodingException {
        return URLEncoder.encode(nullToEmpty(value), StandardCharsets.UTF_8.name()).replace("+", "%20");
    }
    
    private String encodeQueryValue(String value) throws UnsupportedEncodingException {
        return URLEncoder.encode(nullToEmpty(value), StandardCharsets.UTF_8.name());
    }
    
    private String trimTrailingSlash(String value) throws NacosException {
        if (StringUtils.isBlank(value)) {
            throw invalid("SkillHub import source endpoint must not be empty.");
        }
        String result = value.trim();
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }
    
    private String nullToEmpty(String value) {
        return value == null ? "" : value;
    }
    
    private String firstText(JsonNode item, String... keys) {
        for (String key : keys) {
            String value = textOrEmpty(item.get(key));
            if (StringUtils.isNotBlank(value)) {
                return value;
            }
        }
        return "";
    }
    
    private String textOrEmpty(JsonNode node) {
        if (node == null || node.isNull()) {
            return "";
        }
        if (node.isTextual() || node.isNumber() || node.isBoolean()) {
            return node.asText().trim();
        }
        return "";
    }
    
    private String sha256Hex(byte[] data) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(data);
        StringBuilder result = new StringBuilder(hash.length * 2);
        for (byte b : hash) {
            result.append(String.format("%02x", b));
        }
        return result.toString();
    }
    
    private NacosException invalid(String message) {
        return new NacosApiException(NacosException.INVALID_PARAM, ErrorCode.PARAMETER_VALIDATE_ERROR,
                message);
    }
    
    private NacosException dataAccess(String message, Throwable cause) {
        return new NacosApiException(NacosException.SERVER_ERROR, ErrorCode.DATA_ACCESS_ERROR, cause,
                message);
    }
    
    static class SkillHubRemoteSkill {
        
        private final String canonicalSlug;
        
        private final String localName;
        
        private final String version;
        
        private final String description;
        
        private final String namespace;
        
        SkillHubRemoteSkill(String canonicalSlug, String localName, String version,
                String description) {
            this(canonicalSlug, localName, version, description, null);
        }
        
        SkillHubRemoteSkill(String canonicalSlug, String localName, String version,
                String description, String namespace) {
            this.canonicalSlug = canonicalSlug;
            this.localName = localName;
            this.version = version;
            this.description = description == null ? "" : description;
            this.namespace = namespace;
        }
        
        public String getCanonicalSlug() {
            return canonicalSlug;
        }
        
        public String getLocalName() {
            return localName;
        }
        
        public String getVersion() {
            return version;
        }
        
        public String getDescription() {
            return description;
        }
        
        public String getNamespace() {
            return namespace;
        }
    }
    
    static class RedirectRewrite {
        
        private final String fetchUrl;
        
        private final String hostHeader;
        
        RedirectRewrite(String fetchUrl, String hostHeader) {
            this.fetchUrl = fetchUrl;
            this.hostHeader = hostHeader;
        }
        
        public String getFetchUrl() {
            return fetchUrl;
        }
        
        public String getHostHeader() {
            return hostHeader;
        }
    }
    
    private static class ListStrategy {
        
        private final String path;
        
        private final String query;
        
        ListStrategy(String path, String query) {
            this.path = path;
            this.query = query;
        }
    }
}
