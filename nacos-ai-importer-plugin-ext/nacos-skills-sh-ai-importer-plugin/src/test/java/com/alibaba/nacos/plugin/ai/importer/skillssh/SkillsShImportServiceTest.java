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
import com.alibaba.nacos.api.plugin.ConfigItemDefinition;
import com.alibaba.nacos.api.plugin.ConfigItemEffectMode;
import com.alibaba.nacos.plugin.ai.importer.AiResourceImportConstants;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportArtifact;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportCandidatePage;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportContext;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportItem;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportPayloadKind;
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.SkillsShHttpClient;
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.SkillsShHttpResponse;
import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.zip.ZipInputStream;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

/**
 * Unit tests for {@link SkillsShImportService}.
 *
 * @author elnafateh
 */
public class SkillsShImportServiceTest {

    @Test
    public void testBuilderExposesConfigSpec() throws Exception {
        SkillsShImportServiceBuilder builder = new SkillsShImportServiceBuilder();

        assertEquals(SkillsShImportServiceBuilder.PLUGIN_NAME, builder.pluginName());
        assertEquals(SkillsShImportServiceBuilder.IMPORTER_TYPE, builder.importerType());
        assertNotEquals("skills-sh", builder.pluginName());
        assertEquals("skills.sh Authenticated", builder.displayName());
        assertEquals("Import Skills from authenticated skills.sh v1 APIs.",
                builder.description());
        assertEquals(java.util.Collections.singleton(AiResourceImportConstants.RESOURCE_TYPE_SKILL),
                builder.supportedResourceTypes());

        Map<String, ConfigItemDefinition> definitions = definitions(builder);
        assertTrue(builder.isConfigurable());
        assertEquals(10, definitions.size());
        assertTrue(definitions.get(SkillsShImportServiceBuilder.CONFIG_TOKEN).isSensitive());
        assertTrue(definitions.get(SkillsShImportServiceBuilder.CONFIG_TOKEN).getAliases()
                .contains("nacos.plugin.ai.importer.skills.skills-sh.authToken"));
        assertEquals(ConfigItemEffectMode.RESTART,
                definitions.get(AiResourceImportConstants.CONFIG_ENDPOINT).getEffectMode());
        assertEquals(ConfigItemEffectMode.RUNTIME,
                definitions.get(SkillsShImportServiceBuilder.CONFIG_TOKEN).getEffectMode());
        assertEquals(ConfigItemEffectMode.RUNTIME,
                definitions.get(SkillsShImportServiceBuilder.CONFIG_CONNECT_TIMEOUT_MILLIS)
                        .getEffectMode());
        assertEquals(ConfigItemEffectMode.RUNTIME,
                definitions.get(SkillsShImportServiceBuilder.CONFIG_READ_TIMEOUT_MILLIS)
                        .getEffectMode());
        assertEquals(ConfigItemEffectMode.RUNTIME,
                definitions.get(AiResourceImportConstants.CONFIG_DISPLAY_NAME).getEffectMode());

        Map<String, String> config = new HashMap<String, String>();
        config.put(AiResourceImportConstants.CONFIG_ENDPOINT, " https://api.skills.example ");
        config.put(SkillsShImportServiceBuilder.CONFIG_TOKEN, " secret-token ");
        config.put(AiResourceImportConstants.CONFIG_ALLOW_PRIVATE_NETWORK, "true");
        config.put(AiResourceImportConstants.CONFIG_DISPLAY_NAME, "Private skills");
        config.put(AiResourceImportConstants.CONFIG_DESCRIPTION, "Private skills source");
        config.put(SkillsShImportServiceBuilder.CONFIG_CONNECT_TIMEOUT_MILLIS, "1234");
        config.put(SkillsShImportServiceBuilder.CONFIG_READ_TIMEOUT_MILLIS, "5678");
        config.put(AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT, "9");
        config.put(AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE, "99");
        builder.applyConfig(config);

        assertEquals("Private skills", builder.displayName());
        assertEquals("Private skills source", builder.description());
        assertEquals("https://api.skills.example",
                builder.getCurrentConfig().get(AiResourceImportConstants.CONFIG_ENDPOINT));
        assertEquals("secret-token",
                builder.getCurrentConfig().get(SkillsShImportServiceBuilder.CONFIG_TOKEN));
        assertTrue(builder.build() instanceof SkillsShImportService);
    }

    @Test
    public void testSearchReturnsCandidates() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        SkillsShImportService service = new SkillsShImportService(defaultConfig(), client);
        AiResourceImportContext context = newContext();
        context.setQuery("react native");
        context.setLimit(2);
        AiResourceImportCandidatePage result = service.search(context);
        assertEquals("https://skills.sh/api/v1/skills/search?q=react+native&limit=2", client.lastUrl);
        assertEquals(1, result.getItems().size());
        assertFalse(result.isHasMore());
        assertEquals("expo/skills/react-native", result.getItems().get(0).getExternalId());
        assertEquals("React Native", result.getItems().get(0).getName());
        assertEquals("skill", result.getItems().get(0).getResourceType());
        assertEquals("https://skills.sh/expo/skills/react-native",
                result.getItems().get(0).getMetadata().get("artifactUrl"));
        assertEquals("expo/skills", result.getItems().get(0).getMetadata().get("repositorySource"));
        assertEquals("react-native", result.getItems().get(0).getMetadata().get("skillId"));
        assertEquals("github", result.getItems().get(0).getMetadata().get("sourceType"));
        assertEquals("3842", result.getItems().get(0).getMetadata().get("installs"));
    }

    @Test
    public void testSearchUsesDefaultQuery() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        SkillsShImportService service = new SkillsShImportService(defaultConfig(), client);
        service.search(newContext());
        assertEquals("https://skills.sh/api/v1/skills/search?q=skill&limit=30", client.lastUrl);
    }

    @Test(expected = NacosException.class)
    public void testSearchRejectsShortQuery() throws Exception {
        AiResourceImportContext context = newContext();
        context.setQuery("a");
        new SkillsShImportService(defaultConfig(), new FakeHttpClient()).search(context);
    }

    @Test
    public void testFetchReturnsSkillZipArtifact() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        SkillsShImportService service = new SkillsShImportService(defaultConfig(), client);
        AiResourceImportArtifact result = service.fetch(newContext(), item("expo/skills/react-native"));
        assertEquals("https://skills.sh/api/v1/skills/expo/skills/react-native", client.lastUrl);
        assertEquals("skill", result.getResourceType());
        assertEquals("expo/skills/react-native", result.getExternalId());
        assertEquals(AiResourceImportPayloadKind.SKILL_ZIP, result.getPayloadKind());
        assertEquals("hash-1", result.getChecksum());
        assertEquals("hash-1", result.getSourceMetadata().get("hash"));
        assertZipEntryContains(result.getPayload(), "react-native/SKILL.md", "name: React Native");
        assertZipEntryContains(result.getPayload(), "react-native/examples/app.ts", "Example code");
    }

    @Test
    public void testFetchUsesSelectedItemMetadata() throws Exception {
        AiResourceImportItem item = new AiResourceImportItem();
        item.setName("RN");
        Map<String, String> metadata = new HashMap<String, String>();
        metadata.put("repositorySource", "expo/skills");
        metadata.put("skillId", "react-native");
        metadata.put("artifactUrl", "https://skills.sh/expo/skills/react-native");
        item.setMetadata(metadata);
        AiResourceImportArtifact result = new SkillsShImportService(defaultConfig(),
                new FakeHttpClient()).fetch(newContext(), item);
        assertEquals("RN", result.getName());
        assertEquals("expo/skills/react-native", result.getExternalId());
    }

    @Test(expected = NacosException.class)
    public void testFetchRejectsMissingMarkdown() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.detailBody = "{\"id\":\"owner/repo/skill\",\"source\":\"owner/repo\","
                + "\"slug\":\"skill\",\"files\":[{\"path\":\"README.md\",\"contents\":\"x\"}]}";
        new SkillsShImportService(defaultConfig(), client).fetch(newContext(),
                item("owner/repo/skill"));
    }

    @Test(expected = NacosException.class)
    public void testFetchRejectsUnsafePath() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.detailBody = "{\"files\":[{\"path\":\"../SKILL.md\",\"contents\":\"x\"}]}";
        new SkillsShImportService(defaultConfig(), client).fetch(newContext(),
                item("owner/repo/skill"));
    }

    @Test(expected = NacosException.class)
    public void testFetchRejectsSizeLimit() throws Exception {
        SkillsShImportConfig config = config("https://skills.sh", "", false, false, 3000,
                10000, 10, 1);
        new SkillsShImportService(config, new FakeHttpClient()).fetch(newContext(),
                item("expo/skills/react-native"));
    }

    @Test(expected = NacosException.class)
    public void testFetchRejectsHttpError() throws Exception {
        FakeHttpClient client = new FakeHttpClient();
        client.status = 500;
        new SkillsShImportService(defaultConfig(), client).fetch(newContext(),
                item("expo/skills/react-native"));
    }

    private AiResourceImportContext newContext() {
        return new AiResourceImportContext();
    }

    private Map<String, ConfigItemDefinition> definitions(SkillsShImportServiceBuilder builder) {
        List<ConfigItemDefinition> definitions = builder.getConfigDefinitions();
        return definitions.stream().collect(
                Collectors.toMap(ConfigItemDefinition::getKey, definition -> definition));
    }

    private SkillsShImportConfig defaultConfig() {
        return config("https://skills.sh", "", false, false, 3000, 10000, 10,
                10L * 1024L * 1024L);
    }

    private SkillsShImportConfig config(String endpoint, String token, boolean allowHttp,
            boolean allowPrivateNetwork, int connectTimeoutMillis, int readTimeoutMillis,
            int maxItemCount, long maxArtifactSize) {
        Map<String, String> values = new HashMap<String, String>();
        values.put(AiResourceImportConstants.CONFIG_ENDPOINT, endpoint);
        values.put(SkillsShImportServiceBuilder.CONFIG_TOKEN, token);
        values.put(AiResourceImportConstants.CONFIG_ALLOW_HTTP, Boolean.toString(allowHttp));
        values.put(AiResourceImportConstants.CONFIG_ALLOW_PRIVATE_NETWORK,
                Boolean.toString(allowPrivateNetwork));
        values.put(AiResourceImportConstants.CONFIG_DISPLAY_NAME, "skills.sh Authenticated");
        values.put(AiResourceImportConstants.CONFIG_DESCRIPTION,
                "Import Skills from authenticated skills.sh v1 APIs.");
        values.put(SkillsShImportServiceBuilder.CONFIG_CONNECT_TIMEOUT_MILLIS,
                Integer.toString(connectTimeoutMillis));
        values.put(SkillsShImportServiceBuilder.CONFIG_READ_TIMEOUT_MILLIS,
                Integer.toString(readTimeoutMillis));
        values.put(AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT,
                Integer.toString(maxItemCount));
        values.put(AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE,
                Long.toString(maxArtifactSize));
        return new SkillsShImportConfig(values, endpoint, token, allowHttp, allowPrivateNetwork,
                "skills.sh Authenticated", "Import Skills from authenticated skills.sh v1 APIs.",
                connectTimeoutMillis, readTimeoutMillis, maxItemCount, maxArtifactSize);
    }

    private AiResourceImportItem item(String externalId) {
        AiResourceImportItem item = new AiResourceImportItem();
        item.setExternalId(externalId);
        item.setName("react-native");
        return item;
    }

    private void assertZipEntryContains(byte[] zipBytes, String entryName, String expected) throws Exception {
        try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(zipBytes), StandardCharsets.UTF_8)) {
            java.util.zip.ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (entryName.equals(entry.getName())) {
                    ByteArrayOutputStream output = new ByteArrayOutputStream();
                    byte[] buffer = new byte[1024];
                    int len;
                    while ((len = zip.read(buffer)) >= 0) {
                        output.write(buffer, 0, len);
                    }
                    assertTrue(output.toString(StandardCharsets.UTF_8.name()).contains(expected));
                    return;
                }
            }
        }
        throw new AssertionError("Zip entry not found: " + entryName);
    }

    private static class FakeHttpClient implements SkillsShHttpClient {
        private String lastUrl;
        private int status = 200;
        private String detailBody = "{\"id\":\"expo/skills/react-native\",\"source\":\"expo/skills\","
                + "\"slug\":\"react-native\",\"installs\":3842,\"hash\":\"hash-1\","
                + "\"files\":[{\"path\":\"SKILL.md\",\"contents\":\"---\\nname: React Native\\n---\"},"
                + "{\"path\":\"examples/app.ts\",\"contents\":\"// Example code\"}]}";

        @Override
        public SkillsShHttpResponse get(SkillsShImportConfig config, String url) {
            this.lastUrl = url;
            if (url.contains("/search")) {
                String body = "{\"data\":[{\"id\":\"expo/skills/react-native\",\"slug\":\"react-native\","
                        + "\"name\":\"React Native\",\"description\":\"Build apps\",\"source\":\"expo/skills\","
                        + "\"sourceType\":\"github\",\"installs\":3842,\"installUrl\":\"https://github.com/expo/skills\","
                        + "\"url\":\"https://skills.sh/expo/skills/react-native\"}]}";
                return new SkillsShHttpResponse(url, status, body.getBytes(StandardCharsets.UTF_8));
            }
            return new SkillsShHttpResponse(url, status, detailBody.getBytes(StandardCharsets.UTF_8));
        }
    }
}
