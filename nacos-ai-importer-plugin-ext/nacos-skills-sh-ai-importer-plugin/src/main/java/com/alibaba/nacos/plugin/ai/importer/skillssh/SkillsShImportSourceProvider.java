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

import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.AiResourceImportConstants;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.DefaultSkillsShHttpClient;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportSourceProvider;

import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

/**
 * Source preset provider for skills.sh.
 *
 * @author elnafateh
 */
public class SkillsShImportSourceProvider implements AiResourceImportSourceProvider {
    
    public static final String PREFIX = "nacos.plugin.ai.importer.skills.skills-sh.";
    
    public static final String DEFAULT_ENDPOINT = "https://skills.sh";
    
    private static final int DEFAULT_CONNECT_TIMEOUT_MILLIS = 3000;
    
    private static final int DEFAULT_READ_TIMEOUT_MILLIS = 10000;
    
    private static final int DEFAULT_MAX_PAGE_COUNT = 20;
    
    private static final int DEFAULT_MAX_ITEM_COUNT = 500;
    
    private static final long DEFAULT_MAX_ARTIFACT_SIZE = 10L * 1024L * 1024L;
    
    @Override
    public Collection<AiResourceImportSource> loadSources(Properties properties) {
        if (!getBoolean(properties, PREFIX + "enabled", false)) {
            return Collections.emptyList();
        }
        AiResourceImportSource source = new AiResourceImportSource();
        source.setSourceId(getString(properties, "source-id", "sourceId", "skills-sh"));
        source.setDisplayName(getString(properties, "display-name", "displayName", "skills.sh"));
        source.setDescription(getString(properties, "description", "description",
                "Import Skills from the skills.sh API."));
        source.setPluginName(SkillsShImportServiceBuilder.IMPORTER_TYPE);
        source.setResourceTypes(Collections.singletonList(AiResourceImportConstants.RESOURCE_TYPE_SKILL));
        source.setEndpoint(getString(properties, "endpoint", "url", DEFAULT_ENDPOINT));
        source.setEnabled(true);
        source.setAuthRef(getString(properties, "auth-ref", "authRef", null));
        source.setConnectTimeoutMillis(getInt(properties, "connect-timeout-ms", DEFAULT_CONNECT_TIMEOUT_MILLIS));
        source.setReadTimeoutMillis(getInt(properties, "read-timeout-ms", DEFAULT_READ_TIMEOUT_MILLIS));
        source.setMaxPageCount(getInt(properties, "max-page-count", DEFAULT_MAX_PAGE_COUNT));
        source.setMaxItemCount(getInt(properties, "max-item-count", DEFAULT_MAX_ITEM_COUNT));
        source.setMaxArtifactSize(getLong(properties, "max-artifact-size", DEFAULT_MAX_ARTIFACT_SIZE));
        source.setProperties(sourceProperties(properties));
        return Collections.singletonList(source);
    }
    
    private Map<String, String> sourceProperties(Properties properties) {
        Map<String, String> result = new LinkedHashMap<String, String>();
        putConfigured(properties, result, DefaultSkillsShHttpClient.PROPERTY_TOKEN, "token");
        putConfigured(properties, result, DefaultSkillsShHttpClient.PROPERTY_AUTH_TOKEN,
                DefaultSkillsShHttpClient.PROPERTY_AUTH_TOKEN_CAMEL);
        putConfigured(properties, result, DefaultSkillsShHttpClient.PROPERTY_ALLOW_HTTP,
                DefaultSkillsShHttpClient.PROPERTY_ALLOW_HTTP_CAMEL);
        putConfigured(properties, result, DefaultSkillsShHttpClient.PROPERTY_ALLOW_PRIVATE_NETWORK,
                DefaultSkillsShHttpClient.PROPERTY_ALLOW_PRIVATE_NETWORK_CAMEL);
        return result.isEmpty() ? null : result;
    }
    
    private void putConfigured(Properties properties, Map<String, String> target, String kebabKey, String camelKey) {
        String value = getString(properties, kebabKey, camelKey, null);
        if (StringUtils.isNotBlank(value)) {
            target.put(kebabKey, value);
        }
    }
    
    private String getString(Properties properties, String kebabKey, String camelKey, String defaultValue) {
        String value = properties.getProperty(PREFIX + kebabKey);
        if (StringUtils.isBlank(value)) {
            value = properties.getProperty(PREFIX + camelKey);
        }
        return StringUtils.isBlank(value) ? defaultValue : value.trim();
    }
    
    private boolean getBoolean(Properties properties, String key, boolean defaultValue) {
        String value = properties.getProperty(key);
        return StringUtils.isBlank(value) ? defaultValue : Boolean.parseBoolean(value);
    }
    
    private int getInt(Properties properties, String key, int defaultValue) {
        String value = properties.getProperty(PREFIX + key);
        return StringUtils.isBlank(value) ? defaultValue : Integer.parseInt(value);
    }
    
    private long getLong(Properties properties, String key, long defaultValue) {
        String value = properties.getProperty(PREFIX + key);
        return StringUtils.isBlank(value) ? defaultValue : Long.parseLong(value);
    }
}
