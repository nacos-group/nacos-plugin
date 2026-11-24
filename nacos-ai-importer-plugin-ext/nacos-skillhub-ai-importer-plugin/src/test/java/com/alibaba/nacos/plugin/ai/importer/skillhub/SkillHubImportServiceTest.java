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
import com.alibaba.nacos.plugin.ai.importer.AiResourceImportConstants;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportArtifact;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportCandidatePage;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportContext;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportItem;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportPayloadKind;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;
import com.alibaba.nacos.plugin.ai.importer.skillhub.http.SkillHubHttpClient;
import com.alibaba.nacos.plugin.ai.importer.skillhub.http.SkillHubHttpResponse;
import org.junit.Test;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Unit tests for SkillHub importer (Nacos 3.2.x SPI).
 *
 * @author nacos
 */
public class SkillHubImportServiceTest {
    
    @Test
    public void testBuilderAndSourceProvider() throws Exception {
        SkillHubImportServiceBuilder builder = new SkillHubImportServiceBuilder();
        assertEquals(SkillHubImportServiceBuilder.IMPORTER_TYPE, builder.importerType());
        assertTrue(builder.build(new Properties()) instanceof SkillHubImportService);
        
        Properties properties = new Properties();
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "enabled", "true");
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "endpoint",
                "https://hub.example.com");
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "token", "secret");
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "allow-private-network", "true");
        
        Collection<AiResourceImportSource> sources =
                new SkillHubImportSourceProvider().loadSources(properties);
        assertEquals(1, sources.size());
        AiResourceImportSource source = sources.iterator().next();
        assertEquals("skillhub", source.getPluginName());
        assertEquals("https://hub.example.com", source.getEndpoint());
        assertFalse(source.getProperties().containsKey(SkillHubImportSourceProvider.PROPERTY_NAMESPACE));
        assertEquals("secret", source.getProperties().get(SkillHubImportSourceProvider.PROPERTY_TOKEN));
        assertEquals(Collections.singletonList(AiResourceImportConstants.RESOURCE_TYPE_SKILL),
                source.getResourceTypes());
    }
    
    @Test
    public void testSourceProviderOptionalNamespace() throws Exception {
        Properties properties = new Properties();
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "enabled", "true");
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "endpoint",
                "https://hub.example.com");
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "token", "secret");
        properties.setProperty(SkillHubImportSourceProvider.PREFIX + "namespace", "@team-x");
        AiResourceImportSource source =
                new SkillHubImportSourceProvider().loadSources(properties).iterator().next();
        assertEquals("team-x", source.getProperties().get(SkillHubImportSourceProvider.PROPERTY_NAMESPACE));
    }
    
    @Test
    public void testSearchUsesAtNamespaceInQuery() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        SkillHubImportService service = new SkillHubImportService(client);
        AiResourceImportSource source = defaultSource();
        source.getProperties().remove(SkillHubImportSourceProvider.PROPERTY_NAMESPACE);
        AiResourceImportContext context = newContext(source);
        context.setQuery("@team-x alpha");
        context.setLimit(10);
        
        AiResourceImportCandidatePage result = service.search(context);
        assertEquals(1, result.getItems().size());
        assertEquals("team-x--alpha", result.getItems().get(0).getExternalId());
        assertEquals("team-x", result.getItems().get(0).getMetadata().get("namespace"));
        assertTrue(client.urls.get(0).contains("/api/v1/skills?namespaceSlug=team-x"));
    }
    
    @Test
    public void testSearchDefaultsToGlobalWhenNamespaceMissing() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.listBody = "{\"data\":["
                + "{\"slug\":\"alpha\",\"description\":\"global skill\","
                + "\"publishedVersion\":{\"version\":\"1.0.0\"}}"
                + "]}";
        SkillHubImportService service = new SkillHubImportService(client);
        AiResourceImportSource source = defaultSource();
        source.getProperties().remove(SkillHubImportSourceProvider.PROPERTY_NAMESPACE);
        AiResourceImportContext context = newContext(source);
        context.setQuery("alpha");
        
        AiResourceImportCandidatePage result = service.search(context);
        assertEquals(1, result.getItems().size());
        assertEquals("alpha", result.getItems().get(0).getExternalId());
        assertEquals("global", result.getItems().get(0).getMetadata().get("namespace"));
        assertTrue(client.urls.get(0).contains("/api/v1/skills?namespaceSlug=global")
                || client.urls.get(0).contains("/api/v1/search?q="));
    }
    
    @Test
    public void testSearchReturnsCandidatesAndFiltersQuery() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        SkillHubImportService service = new SkillHubImportService(client);
        AiResourceImportContext context = newContext(defaultSource());
        context.setQuery("alpha");
        context.setLimit(10);
        
        AiResourceImportCandidatePage result = service.search(context);
        assertEquals(1, result.getItems().size());
        assertFalse(result.isHasMore());
        assertEquals("team-x--alpha", result.getItems().get(0).getExternalId());
        assertEquals("alpha", result.getItems().get(0).getName());
        assertEquals("1.0.0", result.getItems().get(0).getVersion());
        assertEquals("skill", result.getItems().get(0).getResourceType());
        assertEquals("team-x", result.getItems().get(0).getMetadata().get("namespace"));
        assertEquals("1.0.0", result.getItems().get(0).getMetadata().get("version"));
        assertTrue(client.urls.get(0).contains("/api/v1/skills?namespaceSlug=team-x"));
    }
    
    @Test
    public void testSearchSkipsUnprovenGlobalShortSlug() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.listBody = "{\"data\":["
                + "{\"slug\":\"leaked\",\"description\":\"global leak\",\"version\":\"9.0.0\"},"
                + "{\"slug\":\"team-x--alpha\",\"description\":\"ok\",\"publishedVersion\":{\"version\":\"1.0.0\"}}"
                + "]}";
        SkillHubImportService service = new SkillHubImportService(client);
        AiResourceImportCandidatePage result = service.search(newContext(defaultSource()));
        assertEquals(1, result.getItems().size());
        assertEquals("team-x--alpha", result.getItems().get(0).getExternalId());
    }
    
    @Test
    public void testFetchReturnsSkillZipArtifact() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        SkillHubImportService service = new SkillHubImportService(client);
        AiResourceImportArtifact result = service.fetch(newContext(defaultSource()),
                item("team-x--alpha", "alpha", "1.0.0"));
        assertEquals("skill", result.getResourceType());
        assertEquals("team-x--alpha", result.getExternalId());
        assertEquals("alpha", result.getName());
        assertEquals(AiResourceImportPayloadKind.SKILL_ZIP, result.getPayloadKind());
        assertNotNull(result.getChecksum());
        assertEquals(64, result.getChecksum().length());
        assertTrue(client.urls.get(0).contains(
                "/api/v1/skills/team-x/alpha/versions/1.0.0/download"));
    }
    
    @Test
    public void testFetchFollowsRedirectWithHostRewrite() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.redirectFirstDownload = true;
        AiResourceImportSource source = defaultSource();
        source.getProperties().put(SkillHubImportSourceProvider.PROPERTY_REDIRECT_HOST_MAP,
                "minio:10.0.0.1");
        SkillHubImportService service = new SkillHubImportService(client);
        
        AiResourceImportArtifact result = service.fetch(newContext(source),
                item("team-x--alpha", "alpha", "1.0.0"));
        assertEquals(AiResourceImportPayloadKind.SKILL_ZIP, result.getPayloadKind());
        assertTrue(client.urls.stream().anyMatch(url -> url.startsWith("http://10.0.0.1:9000/")));
        assertEquals("minio:9000", client.lastHostHeader);
    }
    
    @Test
    public void testFetchUsesClawHubCompatibleDownloadFallback() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.failSkillsDownload = true;
        client.redirectClawHubDownload = true;
        SkillHubImportService service = new SkillHubImportService(client);
        
        AiResourceImportArtifact result = service.fetch(newContext(defaultSource()),
                item("team-x--alpha", "alpha", "1.0.0"));
        assertEquals(AiResourceImportPayloadKind.SKILL_ZIP, result.getPayloadKind());
        assertTrue(client.urls.stream().anyMatch(
                url -> url.contains("/api/v1/download/team-x--alpha?version=1.0.0")));
        assertTrue(client.urls.stream().anyMatch(
                url -> url.contains("/api/v1/skills/team-x/alpha/versions/1.0.0/download")));
        assertTrue(client.authFlags.contains(Boolean.TRUE));
    }
    
    @Test
    public void testRewriteRedirectDefaultsMinioToApiHost() throws Exception {
        SkillHubImportConfig config = new SkillHubImportConfig(defaultSource());
        SkillHubImportService service = new SkillHubImportService(new FakeHttpClient());
        SkillHubImportService.RedirectRewrite rewrite = service.rewriteRedirectLocation(config,
                "http://minio:9000/bucket/pkg.zip");
        assertEquals("http://hub.example.com:9000/bucket/pkg.zip", rewrite.getFetchUrl());
        assertEquals("minio:9000", rewrite.getHostHeader());
    }
    
    @Test(expected = NacosException.class)
    public void testFetchRejectsMissingVersion() throws Exception {
        AiResourceImportItem item = new AiResourceImportItem();
        item.setExternalId("team-x--alpha");
        item.setName("alpha");
        new SkillHubImportService(new FakeHttpClient())
                .fetch(newContext(defaultSource()), item);
    }
    
    @Test(expected = NacosException.class)
    public void testFetchRejectsSizeLimit() throws Exception {
        AiResourceImportSource source = defaultSource();
        source.setMaxArtifactSize(1L);
        new SkillHubImportService(new FakeHttpClient())
                .fetch(newContext(source), item("team-x--alpha", "alpha", "1.0.0"));
    }
    
    @Test(expected = NacosException.class)
    public void testFetchRejectsHttpError() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.downloadStatus = 500;
        new SkillHubImportService(client)
                .fetch(newContext(defaultSource()), item("team-x--alpha", "alpha", "1.0.0"));
    }
    
    @Test
    public void testSlugHelpers() {
        assertEquals("team-x", SkillHubSlug.normalizeNamespace("@team-x"));
        assertEquals("team-x--alpha", SkillHubSlug.hubCanonicalSlug("team-x", "alpha"));
        assertEquals("alpha", SkillHubSlug.hubCanonicalSlug("global", "alpha"));
        assertEquals("alpha", SkillHubSlug.localSkillNameFromCanonical("team-x", "team-x--alpha"));
        assertTrue(SkillHubSlug.skillBelongsToNamespace("team-x", "team-x--alpha"));
        assertFalse(SkillHubSlug.skillBelongsToNamespace("team-x", "other--alpha"));
        SkillHubSlug.NamespaceQuery query = SkillHubSlug.parseSearchQuery("@team-x alpha", "");
        assertEquals("team-x", query.getNamespace());
        assertEquals("alpha", query.getKeyword());
        SkillHubSlug.NamespaceQuery slash = SkillHubSlug.parseSearchQuery("@team-x/alpha", "global");
        assertEquals("team-x", slash.getNamespace());
        assertEquals("alpha", slash.getKeyword());
        SkillHubSlug.NamespaceQuery fallback = SkillHubSlug.parseSearchQuery("alpha", "global");
        assertEquals("global", fallback.getNamespace());
        assertEquals("alpha", fallback.getKeyword());
    }
    
    private AiResourceImportContext newContext(AiResourceImportSource source) {
        AiResourceImportContext context = new AiResourceImportContext();
        context.setSource(source);
        return context;
    }
    
    private AiResourceImportSource defaultSource() {
        AiResourceImportSource source = new AiResourceImportSource();
        source.setSourceId("skillhub");
        source.setPluginName(SkillHubImportServiceBuilder.IMPORTER_TYPE);
        source.setEndpoint("https://hub.example.com");
        source.setEnabled(true);
        source.setConnectTimeoutMillis(3000);
        source.setReadTimeoutMillis(30000);
        source.setMaxItemCount(100);
        source.setMaxArtifactSize(10L * 1024L * 1024L);
        source.setResourceTypes(
                Collections.singletonList(AiResourceImportConstants.RESOURCE_TYPE_SKILL));
        Map<String, String> properties = new LinkedHashMap<String, String>();
        properties.put(SkillHubImportSourceProvider.PROPERTY_TOKEN, "token");
        properties.put(SkillHubImportSourceProvider.PROPERTY_NAMESPACE, "team-x");
        properties.put(SkillHubImportSourceProvider.PROPERTY_ALLOW_PRIVATE_NETWORK, "true");
        source.setProperties(properties);
        return source;
    }
    
    private AiResourceImportItem item(String externalId, String name, String version) {
        AiResourceImportItem item = new AiResourceImportItem();
        item.setExternalId(externalId);
        item.setName(name);
        Map<String, String> metadata = new HashMap<String, String>();
        metadata.put("namespace", "team-x");
        metadata.put("skillId", name);
        metadata.put("version", version);
        metadata.put("canonicalSlug", externalId);
        item.setMetadata(metadata);
        return item;
    }
    
    private static byte[] sampleZip() throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (ZipOutputStream zip = new ZipOutputStream(output, StandardCharsets.UTF_8)) {
            zip.putNextEntry(new ZipEntry("alpha/SKILL.md"));
            zip.write("---\nname: alpha\ndescription: demo\n---\n".getBytes(StandardCharsets.UTF_8));
            zip.closeEntry();
        }
        return output.toByteArray();
    }
    
    private static class FakeHttpClient implements SkillHubHttpClient {
        
        private final List<String> urls = new ArrayList<String>();
        
        private final List<Boolean> authFlags = new ArrayList<Boolean>();
        
        private String listBody = "{\"data\":["
                + "{\"slug\":\"team-x--alpha\",\"description\":\"Alpha skill\","
                + "\"publishedVersion\":{\"version\":\"1.0.0\"}},"
                + "{\"slug\":\"team-x--beta\",\"description\":\"Beta skill\","
                + "\"publishedVersion\":{\"version\":\"2.0.0\"}}"
                + "]}";
        
        private int downloadStatus = 200;
        
        private boolean redirectFirstDownload;
        
        private boolean failSkillsDownload;
        
        private boolean redirectClawHubDownload;
        
        private boolean clawHubRedirectSeen;
        
        private String lastHostHeader;
        
        @Override
        public SkillHubHttpResponse get(SkillHubImportConfig config, String url,
                boolean followRedirects, String hostHeader, boolean withAuth) throws Exception {
            urls.add(url);
            authFlags.add(withAuth);
            lastHostHeader = hostHeader;
            if (url.contains("/api/v1/skills?") || url.contains("/api/web/skills")
                    || url.contains("/api/v1/search")) {
                return new SkillHubHttpResponse(url, 200,
                        listBody.getBytes(StandardCharsets.UTF_8));
            }
            if (url.contains("/api/v1/download/") || url.contains("/api/v1/download?")) {
                if (redirectClawHubDownload) {
                    clawHubRedirectSeen = true;
                    return new SkillHubHttpResponse(url, 302, new byte[0],
                            "/api/v1/skills/team-x/alpha/versions/1.0.0/download");
                }
                if (downloadStatus >= 400) {
                    return new SkillHubHttpResponse(url, downloadStatus,
                            "{\"msg\":\"error\"}".getBytes(StandardCharsets.UTF_8));
                }
                return new SkillHubHttpResponse(url, 200, sampleZip());
            }
            if (url.contains("/download") || url.contains(":9000/")) {
                if (failSkillsDownload && url.contains("/api/v1/skills/") && !clawHubRedirectSeen) {
                    return new SkillHubHttpResponse(url, 405,
                            "{\"msg\":\"method not allowed\"}".getBytes(StandardCharsets.UTF_8));
                }
                if (redirectFirstDownload && url.contains("/api/v1/skills/")
                        && !url.contains(":9000/")) {
                    redirectFirstDownload = false;
                    return new SkillHubHttpResponse(url, 302, new byte[0],
                            "http://minio:9000/skillhub-skills/pkg.zip");
                }
                if (downloadStatus >= 400) {
                    return new SkillHubHttpResponse(url, downloadStatus,
                            "{\"msg\":\"error\"}".getBytes(StandardCharsets.UTF_8));
                }
                return new SkillHubHttpResponse(url, 200, sampleZip());
            }
            return new SkillHubHttpResponse(url, 404, new byte[0]);
        }
    }
}
