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

import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Runtime configuration resolved from {@link AiResourceImportSource}.
 *
 * @author nacos
 */
public class SkillHubImportConfig {
    
    private final String endpoint;
    
    private final String token;
    
    private final String namespace;
    
    private final boolean allowHttp;
    
    private final boolean allowPrivateNetwork;
    
    private final int connectTimeoutMillis;
    
    private final int readTimeoutMillis;
    
    private final int maxItemCount;
    
    private final long maxArtifactSize;
    
    private final Map<String, String> redirectHostMap;
    
    public SkillHubImportConfig(AiResourceImportSource source) {
        Map<String, String> properties = source.getProperties() == null
                ? Collections.<String, String>emptyMap()
                : source.getProperties();
        this.endpoint = source.getEndpoint();
        this.token = firstNonBlank(properties.get(SkillHubImportSourceProvider.PROPERTY_TOKEN),
                properties.get("api-token"), properties.get("auth-token"));
        this.namespace = SkillHubSlug.normalizeNamespace(
                firstNonBlank(properties.get(SkillHubImportSourceProvider.PROPERTY_NAMESPACE),
                        properties.get("namespaceSlug")));
        this.allowHttp = Boolean.parseBoolean(
                firstNonBlank(properties.get(SkillHubImportSourceProvider.PROPERTY_ALLOW_HTTP),
                        properties.get("allowHttp"), "false"));
        this.allowPrivateNetwork = Boolean.parseBoolean(firstNonBlank(
                properties.get(SkillHubImportSourceProvider.PROPERTY_ALLOW_PRIVATE_NETWORK),
                properties.get("allowPrivateNetwork"), "false"));
        this.connectTimeoutMillis = source.getConnectTimeoutMillis() > 0
                ? source.getConnectTimeoutMillis() : 3000;
        this.readTimeoutMillis =
                source.getReadTimeoutMillis() > 0 ? source.getReadTimeoutMillis() : 30000;
        this.maxItemCount = source.getMaxItemCount() > 0 ? source.getMaxItemCount() : 500;
        this.maxArtifactSize =
                source.getMaxArtifactSize() > 0 ? source.getMaxArtifactSize() : 10L * 1024L * 1024L;
        this.redirectHostMap = parseRedirectHostMap(
                firstNonBlank(properties.get(SkillHubImportSourceProvider.PROPERTY_REDIRECT_HOST_MAP),
                        properties.get("redirectHostMap"), ""));
    }
    
    public SkillHubImportConfig(String endpoint, String token, String namespace, boolean allowHttp,
            boolean allowPrivateNetwork, int connectTimeoutMillis, int readTimeoutMillis,
            int maxItemCount, long maxArtifactSize, Map<String, String> redirectHostMap) {
        this.endpoint = endpoint;
        this.token = token;
        this.namespace = SkillHubSlug.normalizeNamespace(namespace);
        this.allowHttp = allowHttp;
        this.allowPrivateNetwork = allowPrivateNetwork;
        this.connectTimeoutMillis = connectTimeoutMillis;
        this.readTimeoutMillis = readTimeoutMillis;
        this.maxItemCount = maxItemCount;
        this.maxArtifactSize = maxArtifactSize;
        this.redirectHostMap = redirectHostMap == null
                ? Collections.<String, String>emptyMap()
                : new LinkedHashMap<String, String>(redirectHostMap);
    }
    
    static Map<String, String> parseRedirectHostMap(String raw) {
        Map<String, String> result = new LinkedHashMap<String, String>();
        if (StringUtils.isBlank(raw)) {
            return result;
        }
        String[] parts = raw.split(",");
        for (String part : parts) {
            String piece = part.trim();
            if (StringUtils.isBlank(piece) || !piece.contains(":")) {
                continue;
            }
            int index = piece.indexOf(':');
            String src = piece.substring(0, index).trim();
            String dst = piece.substring(index + 1).trim();
            if (StringUtils.isNotBlank(src) && StringUtils.isNotBlank(dst)) {
                result.put(src, dst);
            }
        }
        return result;
    }
    
    private static String firstNonBlank(String... values) {
        if (values == null) {
            return null;
        }
        for (String each : values) {
            if (StringUtils.isNotBlank(each)) {
                return each.trim();
            }
        }
        return null;
    }
    
    public String getEndpoint() {
        return endpoint;
    }
    
    public String getToken() {
        return token;
    }
    
    public String getNamespace() {
        return namespace;
    }
    
    public boolean isAllowHttp() {
        return allowHttp;
    }
    
    public boolean isAllowPrivateNetwork() {
        return allowPrivateNetwork;
    }
    
    public int getConnectTimeoutMillis() {
        return connectTimeoutMillis;
    }
    
    public int getReadTimeoutMillis() {
        return readTimeoutMillis;
    }
    
    public int getMaxItemCount() {
        return maxItemCount;
    }
    
    public long getMaxArtifactSize() {
        return maxArtifactSize;
    }
    
    public Map<String, String> getRedirectHostMap() {
        return new LinkedHashMap<String, String>(redirectHostMap);
    }
}
