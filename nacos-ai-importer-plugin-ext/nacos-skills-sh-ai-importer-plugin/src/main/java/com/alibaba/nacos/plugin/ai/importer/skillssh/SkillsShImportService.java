/*
 * Copyright 1999-2026 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 */
package com.alibaba.nacos.plugin.ai.importer.skillssh;

import com.alibaba.nacos.api.exception.NacosException;
import com.alibaba.nacos.api.exception.api.NacosApiException;
import com.alibaba.nacos.api.model.v2.ErrorCode;
import com.alibaba.nacos.common.utils.CollectionUtils;
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
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.DefaultSkillsShHttpClient;
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.SkillsShHttpClient;
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.SkillsShHttpResponse;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportService;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.io.ByteArrayOutputStream;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * Importer for the skills.sh API.
 *
 * @author elnafateh
 */
public class SkillsShImportService implements AiResourceImportService {
    
    public static final String RESOURCE_TYPE_SKILL = AiResourceImportConstants.RESOURCE_TYPE_SKILL;
    
    private static final String API_SEARCH = "/api/v1/skills/search";
    
    private static final String API_SKILLS = "/api/v1/skills";
    
    private static final String METADATA_SOURCE = "source";
    
    private static final String METADATA_ARTIFACT_URL = "artifactUrl";
    
    private static final String METADATA_INSTALL_URL = "installUrl";
    
    private static final String METADATA_REPOSITORY_SOURCE = "repositorySource";
    
    private static final String METADATA_SOURCE_TYPE = "sourceType";
    
    private static final String METADATA_SKILL_ID = "skillId";
    
    private static final String METADATA_INSTALLS = "installs";
    
    private static final String METADATA_HASH = "hash";
    
    private static final String SKILL_MARKDOWN_FILE = "SKILL.md";
    
    private static final String DEFAULT_SEARCH_QUERY = "skill";
    
    private static final int MIN_SEARCH_QUERY_LENGTH = 2;
    
    private static final int DEFAULT_LIMIT = 30;
    
    private static final int DEFAULT_MAX_FILE_COUNT = 500;
    
    private final SkillsShHttpClient httpClient;
    
    public SkillsShImportService() {
        this(new DefaultSkillsShHttpClient());
    }
    
    SkillsShImportService(SkillsShHttpClient httpClient) {
        this.httpClient = httpClient;
    }
    
    @Override
    public String importerType() {
        return SkillsShImportServiceBuilder.IMPORTER_TYPE;
    }
    
    @Override
    public Set<String> supportedResourceTypes() {
        return Collections.singleton(RESOURCE_TYPE_SKILL);
    }
    
    @Override
    public AiResourceImportCandidatePage search(AiResourceImportContext context) throws NacosException {
        try {
            AiResourceImportSource source = requireSource(context);
            String apiRoot = resolveApiRoot(source);
            int resultLimit = resolveLimit(context.getLimit());
            SkillsShHttpResponse response = httpClient.get(source, searchUrl(apiRoot, resolveQuery(context.getQuery()), resultLimit));
            if (!response.isSuccess()) {
                throw new IllegalStateException("HTTP " + response.getStatusCode() + " when fetching " + response.getUrl());
            }
            SkillsShSearchResponse searchResponse = JacksonUtils.toObj(response.getBody(), SkillsShSearchResponse.class);
            AiResourceImportCandidatePage result = new AiResourceImportCandidatePage();
            result.setItems(toCandidates(searchResponse, resultLimit));
            result.setHasMore(false);
            result.setNextCursor(null);
            return result;
        } catch (NacosException e) {
            throw e;
        } catch (Exception e) {
            throw dataAccess("Search skills.sh source failed: " + e.getMessage(), e);
        }
    }
    
    @Override
    public AiResourceImportArtifact fetch(AiResourceImportContext context, AiResourceImportItem item) throws NacosException {
        try {
            AiResourceImportSource source = requireSource(context);
            String apiRoot = resolveApiRoot(source);
            SkillsShSkillRef skillRef = resolveSkillRef(item);
            SkillsShHttpResponse response = httpClient.get(source, detailUrl(apiRoot, skillRef.getExternalId()));
            if (!response.isSuccess()) {
                throw new IllegalStateException("HTTP " + response.getStatusCode() + " when fetching " + response.getUrl());
            }
            SkillsShDetailResponse detailResponse = JacksonUtils.toObj(response.getBody(), SkillsShDetailResponse.class);
            byte[] zipBytes = toSkillZip(source, skillRef, detailResponse);
            AiResourceImportArtifact result = new AiResourceImportArtifact();
            result.setResourceType(RESOURCE_TYPE_SKILL);
            result.setExternalId(skillRef.getExternalId());
            result.setName(skillRef.getName());
            result.setPayloadKind(AiResourceImportPayloadKind.SKILL_ZIP);
            result.setPayload(zipBytes);
            result.setChecksum(detailResponse.getHash());
            result.setSourceMetadata(buildArtifactMetadata(skillRef, detailResponse));
            return result;
        } catch (NacosException e) {
            throw e;
        } catch (Exception e) {
            throw dataAccess("Fetch skills.sh artifact failed: " + e.getMessage(), e);
        }
    }
    
    private AiResourceImportSource requireSource(AiResourceImportContext context) throws NacosException {
        if (context == null || context.getSource() == null || StringUtils.isBlank(context.getSource().getEndpoint())) {
            throw invalid("skills.sh import source endpoint must not be empty.");
        }
        return context.getSource();
    }
    
    private int resolveLimit(int limit) {
        return limit <= 0 ? DEFAULT_LIMIT : limit;
    }
    
    private String resolveQuery(String query) throws NacosException {
        if (StringUtils.isBlank(query)) {
            return DEFAULT_SEARCH_QUERY;
        }
        String result = query.trim();
        if (result.length() < MIN_SEARCH_QUERY_LENGTH) {
            throw invalid("skills.sh search query must be at least 2 characters.");
        }
        return result;
    }
    
    private List<AiResourceImportCandidate> toCandidates(SkillsShSearchResponse searchResponse, int limit) throws NacosException {
        if (searchResponse == null || CollectionUtils.isEmpty(searchResponse.getData())) {
            return Collections.emptyList();
        }
        List<AiResourceImportCandidate> result = new ArrayList<AiResourceImportCandidate>();
        for (SkillsShSkillSummary each : searchResponse.getData()) {
            if (each == null || StringUtils.isBlank(each.getId())) {
                continue;
            }
            SkillsShSkillRef skillRef = resolveSkillRef(each);
            AiResourceImportCandidate candidate = new AiResourceImportCandidate();
            candidate.setResourceType(RESOURCE_TYPE_SKILL);
            candidate.setExternalId(skillRef.getExternalId());
            candidate.setName(skillRef.getName());
            candidate.setDescription(each.getDescription());
            candidate.setMetadata(buildCandidateMetadata(skillRef, each));
            result.add(candidate);
            if (result.size() >= limit) {
                break;
            }
        }
        return result;
    }
    
    private SkillsShSkillRef resolveSkillRef(SkillsShSkillSummary item) throws NacosException {
        SkillsShSkillRef result = resolveSkillRef(item.getId(), item.getSource(), item.getSlug());
        result.setName(StringUtils.isBlank(item.getName()) ? result.getSkillId() : item.getName());
        result.setSourceType(item.getSourceType());
        result.setInstallUrl(item.getInstallUrl());
        result.setUrl(item.getUrl());
        return result;
    }
    
    private SkillsShSkillRef resolveSkillRef(AiResourceImportItem item) throws NacosException {
        if (item == null) {
            throw invalid("skills.sh import item must not be null.");
        }
        Map<String, String> metadata = item.getMetadata();
        String source = metadata == null ? null : metadata.get(METADATA_REPOSITORY_SOURCE);
        String skillId = metadata == null ? null : metadata.get(METADATA_SKILL_ID);
        String externalId = StringUtils.isNotBlank(item.getExternalId()) ? item.getExternalId() : item.getName();
        SkillsShSkillRef result = resolveSkillRef(externalId, source, skillId);
        result.setName(StringUtils.isBlank(item.getName()) ? result.getSkillId() : item.getName());
        if (metadata != null) {
            result.setSourceType(metadata.get(METADATA_SOURCE_TYPE));
            result.setInstallUrl(metadata.get(METADATA_INSTALL_URL));
            result.setUrl(metadata.get(METADATA_ARTIFACT_URL));
        }
        return result;
    }
    
    private SkillsShSkillRef resolveSkillRef(String externalId, String source, String skillId) throws NacosException {
        if (StringUtils.isBlank(source) || StringUtils.isBlank(skillId)) {
            String[] segments = StringUtils.isBlank(externalId) ? new String[0] : externalId.split("/");
            if (segments.length >= 2) {
                skillId = segments[segments.length - 1];
                source = joinSegments(segments, 0, segments.length - 1);
            }
        }
        if (StringUtils.isBlank(source) || StringUtils.isBlank(skillId)) {
            throw invalid("skills.sh import item must include source and skill id.");
        }
        validatePathSafety(source);
        validatePathSafety(skillId);
        return new SkillsShSkillRef(source.trim(), skillId.trim());
    }
    
    private String joinSegments(String[] segments, int startIndex, int endIndex) {
        StringBuilder result = new StringBuilder();
        for (int i = startIndex; i < endIndex; i++) {
            if (result.length() > 0) {
                result.append('/');
            }
            result.append(segments[i]);
        }
        return result.toString();
    }
    
    private byte[] toSkillZip(AiResourceImportSource source, SkillsShSkillRef skillRef, SkillsShDetailResponse detail)
            throws Exception {
        if (detail == null || CollectionUtils.isEmpty(detail.getFiles())) {
            throw invalid("skills.sh detail response does not contain skill files.");
        }
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        Set<String> entryNames = new HashSet<String>();
        boolean hasSkillMarkdown = false;
        long totalSize = 0;
        int fileCount = 0;
        try (ZipOutputStream zip = new ZipOutputStream(output, StandardCharsets.UTF_8)) {
            for (SkillsShFileSnapshot each : detail.getFiles()) {
                String path = normalizeFilePath(each == null ? null : each.getPath());
                if (StringUtils.isBlank(path)) {
                    continue;
                }
                if (++fileCount > resolveMaxFileCount(source)) {
                    throw invalid("skills.sh detail response contains too many files.");
                }
                validatePathSafety(path);
                byte[] bytes = nullToEmpty(each.getContents()).getBytes(StandardCharsets.UTF_8);
                checkDownloadedSize(source, totalSize + bytes.length);
                totalSize += bytes.length;
                String entryName = skillRef.getSkillId() + "/" + path;
                validatePathSafety(entryName);
                if (!entryNames.add(entryName)) {
                    continue;
                }
                hasSkillMarkdown = hasSkillMarkdown || SKILL_MARKDOWN_FILE.equalsIgnoreCase(path);
                zip.putNextEntry(new ZipEntry(entryName));
                zip.write(bytes);
                zip.closeEntry();
            }
        }
        if (!hasSkillMarkdown) {
            throw invalid("skills.sh detail response must contain SKILL.md.");
        }
        return output.toByteArray();
    }
    
    private int resolveMaxFileCount(AiResourceImportSource source) {
        return source.getMaxItemCount() > 0 ? source.getMaxItemCount() : DEFAULT_MAX_FILE_COUNT;
    }
    
    private String normalizeFilePath(String path) {
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
        if (StringUtils.isBlank(path) || path.startsWith("/") || path.endsWith("/") || path.contains("\\")) {
            throw invalid("skills.sh path is invalid: " + path);
        }
        String[] segments = path.split("/");
        for (String segment : segments) {
            if (StringUtils.isBlank(segment) || ".".equals(segment) || "..".equals(segment) || segment.startsWith(".")) {
                throw invalid("skills.sh path is invalid: " + path);
            }
        }
    }
    
    private void checkDownloadedSize(AiResourceImportSource source, long totalSize) throws NacosException {
        if (source.getMaxArtifactSize() > 0 && totalSize > source.getMaxArtifactSize()) {
            throw invalid("skills.sh artifact size exceeds source limit.");
        }
    }
    
    private Map<String, String> buildCandidateMetadata(SkillsShSkillRef skillRef, SkillsShSkillSummary item) {
        Map<String, String> metadata = baseMetadata(skillRef);
        putIfNotBlank(metadata, METADATA_SOURCE_TYPE, item.getSourceType());
        putIfNotBlank(metadata, METADATA_INSTALL_URL, item.getInstallUrl());
        if (item.getInstalls() != null) {
            metadata.put(METADATA_INSTALLS, String.valueOf(item.getInstalls()));
        }
        return metadata;
    }
    
    private Map<String, String> buildArtifactMetadata(SkillsShSkillRef skillRef, SkillsShDetailResponse detail) {
        Map<String, String> metadata = baseMetadata(skillRef);
        putIfNotBlank(metadata, METADATA_SOURCE_TYPE, skillRef.getSourceType());
        putIfNotBlank(metadata, METADATA_INSTALL_URL, skillRef.getInstallUrl());
        putIfNotBlank(metadata, METADATA_HASH, detail.getHash());
        if (detail.getInstalls() != null) {
            metadata.put(METADATA_INSTALLS, String.valueOf(detail.getInstalls()));
        }
        return metadata;
    }
    
    private Map<String, String> baseMetadata(SkillsShSkillRef skillRef) {
        Map<String, String> metadata = new LinkedHashMap<String, String>();
        putIfNotBlank(metadata, METADATA_SOURCE, skillRef.getUrl());
        putIfNotBlank(metadata, METADATA_ARTIFACT_URL, skillRef.getUrl());
        metadata.put(METADATA_REPOSITORY_SOURCE, skillRef.getSource());
        metadata.put(METADATA_SKILL_ID, skillRef.getSkillId());
        return metadata;
    }
    
    private void putIfNotBlank(Map<String, String> metadata, String key, String value) {
        if (StringUtils.isNotBlank(value)) {
            metadata.put(key, value);
        }
    }
    
    private String resolveApiRoot(AiResourceImportSource source) throws NacosException {
        String endpoint = trimTrailingSlash(source.getEndpoint());
        if (endpoint.endsWith(API_SEARCH)) {
            return endpoint.substring(0, endpoint.length() - API_SEARCH.length());
        }
        if (endpoint.endsWith(API_SKILLS)) {
            return endpoint.substring(0, endpoint.length() - API_SKILLS.length());
        }
        return endpoint;
    }
    
    private String searchUrl(String apiRoot, String query, int limit) throws UnsupportedEncodingException {
        return apiRoot + API_SEARCH + "?q=" + encodeQueryValue(query) + "&limit=" + limit;
    }
    
    private String detailUrl(String apiRoot, String externalId) throws UnsupportedEncodingException {
        return apiRoot + API_SKILLS + "/" + encodePath(externalId);
    }
    
    private String encodePath(String path) throws UnsupportedEncodingException {
        String[] segments = path.split("/");
        StringBuilder result = new StringBuilder();
        for (String each : segments) {
            if (result.length() > 0) {
                result.append('/');
            }
            result.append(URLEncoder.encode(each, StandardCharsets.UTF_8.name()).replace("+", "%20"));
        }
        return result.toString();
    }
    
    private String encodeQueryValue(String value) throws UnsupportedEncodingException {
        return URLEncoder.encode(nullToEmpty(value), StandardCharsets.UTF_8.name());
    }
    
    private String trimTrailingSlash(String value) throws NacosException {
        if (StringUtils.isBlank(value)) {
            throw invalid("skills.sh import source endpoint must not be empty.");
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
    
    private NacosException invalid(String message) {
        return new NacosApiException(NacosException.INVALID_PARAM, ErrorCode.PARAMETER_VALIDATE_ERROR, message);
    }
    
    private NacosException dataAccess(String message, Throwable cause) {
        return new NacosApiException(NacosException.SERVER_ERROR, ErrorCode.DATA_ACCESS_ERROR, cause, message);
    }
    
    @JsonIgnoreProperties(ignoreUnknown = true)
    static class SkillsShSearchResponse {
        private List<SkillsShSkillSummary> data;
        public List<SkillsShSkillSummary> getData() { return data; }
        public void setData(List<SkillsShSkillSummary> data) { this.data = data; }
    }
    
    @JsonIgnoreProperties(ignoreUnknown = true)
    static class SkillsShSkillSummary {
        private String id;
        private String slug;
        private String name;
        private String description;
        private String source;
        private String sourceType;
        private Integer installs;
        private String installUrl;
        private String url;
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getSlug() { return slug; }
        public void setSlug(String slug) { this.slug = slug; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public String getSource() { return source; }
        public void setSource(String source) { this.source = source; }
        public String getSourceType() { return sourceType; }
        public void setSourceType(String sourceType) { this.sourceType = sourceType; }
        public Integer getInstalls() { return installs; }
        public void setInstalls(Integer installs) { this.installs = installs; }
        public String getInstallUrl() { return installUrl; }
        public void setInstallUrl(String installUrl) { this.installUrl = installUrl; }
        public String getUrl() { return url; }
        public void setUrl(String url) { this.url = url; }
    }
    
    @JsonIgnoreProperties(ignoreUnknown = true)
    static class SkillsShDetailResponse {
        private String id;
        private String source;
        private String slug;
        private Integer installs;
        private String hash;
        private List<SkillsShFileSnapshot> files;
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getSource() { return source; }
        public void setSource(String source) { this.source = source; }
        public String getSlug() { return slug; }
        public void setSlug(String slug) { this.slug = slug; }
        public Integer getInstalls() { return installs; }
        public void setInstalls(Integer installs) { this.installs = installs; }
        public String getHash() { return hash; }
        public void setHash(String hash) { this.hash = hash; }
        public List<SkillsShFileSnapshot> getFiles() { return files; }
        public void setFiles(List<SkillsShFileSnapshot> files) { this.files = files; }
    }
    
    @JsonIgnoreProperties(ignoreUnknown = true)
    static class SkillsShFileSnapshot {
        private String path;
        private String contents;
        public String getPath() { return path; }
        public void setPath(String path) { this.path = path; }
        public String getContents() { return contents; }
        public void setContents(String contents) { this.contents = contents; }
    }
    
    static class SkillsShSkillRef {
        private final String source;
        private final String skillId;
        private String name;
        private String sourceType;
        private String installUrl;
        private String url;
        SkillsShSkillRef(String source, String skillId) {
            this.source = source;
            this.skillId = skillId;
            this.name = skillId;
            this.url = "https://skills.sh/" + getExternalId();
        }
        public String getSource() { return source; }
        public String getSkillId() { return skillId; }
        public String getExternalId() { return source + "/" + skillId; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getSourceType() { return sourceType; }
        public void setSourceType(String sourceType) { this.sourceType = sourceType; }
        public String getInstallUrl() { return installUrl; }
        public void setInstallUrl(String installUrl) { this.installUrl = installUrl; }
        public String getUrl() { return url; }
        public void setUrl(String url) { if (StringUtils.isNotBlank(url)) { this.url = url; } }
    }
}
