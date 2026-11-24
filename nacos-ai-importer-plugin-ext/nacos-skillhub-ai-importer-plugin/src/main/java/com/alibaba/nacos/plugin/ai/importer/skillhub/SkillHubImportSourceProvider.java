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
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.AiResourceImportConstants;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportSourceProvider;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

/**
 * Registers the SkillHub import source from application.properties (Nacos 3.2.x SPI).
 *
 * <p>Prefix: {@code nacos.plugin.ai.importer.skills.skillhub.}
 *
 * @author nacos
 */
public class SkillHubImportSourceProvider implements AiResourceImportSourceProvider {
    
    public static final String PREFIX = "nacos.plugin.ai.importer.skills.skillhub.";
    
    public static final String PROPERTY_TOKEN = "token";
    
    public static final String PROPERTY_NAMESPACE = "namespace";
    
    public static final String PROPERTY_REDIRECT_HOST_MAP = "redirect-host-map";
    
    public static final String PROPERTY_ALLOW_HTTP = "allow-http";
    
    public static final String PROPERTY_ALLOW_PRIVATE_NETWORK = "allow-private-network";
    
    private static final int DEFAULT_CONNECT_TIMEOUT_MILLIS = 3000;
    
    private static final int DEFAULT_READ_TIMEOUT_MILLIS = 30000;
    
    private static final int DEFAULT_MAX_PAGE_COUNT = 20;
    
    private static final int DEFAULT_MAX_ITEM_COUNT = 500;
    
    private static final long DEFAULT_MAX_ARTIFACT_SIZE = 10L * 1024L * 1024L;
    
    @Override
    public Collection<AiResourceImportSource> loadSources(Properties properties)
            throws NacosException {
        if (!getBoolean(properties, PREFIX + "enabled", false)) {
            return Collections.emptyList();
        }
        String endpoint = getString(properties, PREFIX, "endpoint", "url", null);
        if (StringUtils.isBlank(endpoint)) {
            throw invalidConfig("SkillHub import source endpoint must not be empty when enabled.");
        }
        String token = getString(properties, PREFIX, PROPERTY_TOKEN, "api-token", null);
        if (StringUtils.isBlank(token)) {
            throw invalidConfig("SkillHub import source token must not be empty when enabled.");
        }
        // Optional default namespace. Search may override with options.namespace or "@ns ..." query.
        String namespace = SkillHubSlug.normalizeNamespace(
                getString(properties, PREFIX, PROPERTY_NAMESPACE, "namespaceSlug", null));
        
        AiResourceImportSource result = new AiResourceImportSource();
        result.setSourceId(getString(properties, PREFIX, "source-id", "sourceId", "skillhub"));
        result.setDisplayName(
                getString(properties, PREFIX, "display-name", "displayName", "SkillHub"));
        result.setDescription(getString(properties, PREFIX, "description", "description",
                "Import Skills from an authenticated SkillHub registry. "
                        + "Default namespace is global; use @namespace or @namespace keyword to switch."));
        result.setPluginName(SkillHubImportServiceBuilder.IMPORTER_TYPE);
        result.setResourceTypes(
                Collections.singletonList(AiResourceImportConstants.RESOURCE_TYPE_SKILL));
        result.setEndpoint(endpoint);
        result.setEnabled(true);
        result.setAuthRef(getString(properties, PREFIX, "auth-ref", "authRef", null));
        result.setConnectTimeoutMillis(
                getInt(properties, PREFIX + "connect-timeout-ms", DEFAULT_CONNECT_TIMEOUT_MILLIS));
        result.setReadTimeoutMillis(
                getInt(properties, PREFIX + "read-timeout-ms", DEFAULT_READ_TIMEOUT_MILLIS));
        result.setMaxPageCount(getInt(properties, PREFIX + "max-page-count", DEFAULT_MAX_PAGE_COUNT));
        result.setMaxItemCount(getInt(properties, PREFIX + "max-item-count", DEFAULT_MAX_ITEM_COUNT));
        result.setMaxArtifactSize(
                getLong(properties, PREFIX + "max-artifact-size", DEFAULT_MAX_ARTIFACT_SIZE));
        
        Map<String, String> sourceProperties = new LinkedHashMap<String, String>();
        sourceProperties.put(PROPERTY_TOKEN, token.trim());
        if (StringUtils.isNotBlank(namespace)) {
            sourceProperties.put(PROPERTY_NAMESPACE, namespace);
        }
        putIfPresent(properties, PREFIX, PROPERTY_ALLOW_HTTP, "allowHttp", sourceProperties);
        putIfPresent(properties, PREFIX, PROPERTY_ALLOW_PRIVATE_NETWORK, "allowPrivateNetwork",
                sourceProperties);
        putIfPresent(properties, PREFIX, PROPERTY_REDIRECT_HOST_MAP, "redirectHostMap",
                sourceProperties);
        result.setProperties(sourceProperties);
        
        List<AiResourceImportSource> sources = new ArrayList<AiResourceImportSource>(1);
        sources.add(result);
        return sources;
    }
    
    private void putIfPresent(Properties properties, String prefix, String kebabKey, String camelKey,
            Map<String, String> target) {
        String value = getString(properties, prefix, kebabKey, camelKey, null);
        if (StringUtils.isNotBlank(value)) {
            target.put(kebabKey, value.trim());
        }
    }
    
    private String getString(Properties properties, String prefix, String kebabKey, String camelKey,
            String defaultValue) {
        String value = properties.getProperty(prefix + kebabKey);
        if (StringUtils.isBlank(value)) {
            value = properties.getProperty(prefix + camelKey);
        }
        return StringUtils.isBlank(value) ? defaultValue : value.trim();
    }
    
    private boolean getBoolean(Properties properties, String key, boolean defaultValue) {
        String value = properties.getProperty(key);
        return StringUtils.isBlank(value) ? defaultValue : Boolean.parseBoolean(value);
    }
    
    private int getInt(Properties properties, String key, int defaultValue) {
        String value = properties.getProperty(key);
        return StringUtils.isBlank(value) ? defaultValue : Integer.parseInt(value);
    }
    
    private long getLong(Properties properties, String key, long defaultValue) {
        String value = properties.getProperty(key);
        return StringUtils.isBlank(value) ? defaultValue : Long.parseLong(value);
    }
    
    private NacosException invalidConfig(String message) {
        return new NacosApiException(NacosException.INVALID_PARAM,
                ErrorCode.PARAMETER_VALIDATE_ERROR, message);
    }
}
