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
package com.alibaba.nacos.plugin.ai.importer.skillssh;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Immutable configuration snapshot for authenticated skills.sh API access.
 *
 * @author Zhengcy05
 */
public class SkillsShImportConfig {
    
    /*
     * Canonical item-key values returned through PluginConfigSpec#getCurrentConfig().
     * A defensive copy is kept so callers cannot mutate the active snapshot.
     */
    private final Map<String, String> values;
    
    private final String endpoint;
    
    private final String token;
    
    private final boolean allowHttp;
    
    private final boolean allowPrivateNetwork;
    
    private final String displayName;
    
    private final String description;
    
    private final int connectTimeoutMillis;
    
    private final int readTimeoutMillis;
    
    private final int maxItemCount;
    
    private final long maxArtifactSize;
    
    public SkillsShImportConfig(Map<String, String> values, String endpoint, String token,
            boolean allowHttp, boolean allowPrivateNetwork, String displayName,
            String description, int connectTimeoutMillis, int readTimeoutMillis,
            int maxItemCount, long maxArtifactSize) {
        this.values = new LinkedHashMap<String, String>(values);
        this.endpoint = endpoint;
        this.token = token;
        this.allowHttp = allowHttp;
        this.allowPrivateNetwork = allowPrivateNetwork;
        this.displayName = displayName;
        this.description = description;
        this.connectTimeoutMillis = connectTimeoutMillis;
        this.readTimeoutMillis = readTimeoutMillis;
        this.maxItemCount = maxItemCount;
        this.maxArtifactSize = maxArtifactSize;
    }
    
    public Map<String, String> getValues() {
        return new LinkedHashMap<String, String>(values);
    }
    
    public String getEndpoint() {
        return endpoint;
    }
    
    public String getToken() {
        return token;
    }
    
    public boolean isAllowHttp() {
        return allowHttp;
    }
    
    public boolean isAllowPrivateNetwork() {
        return allowPrivateNetwork;
    }
    
    public String getDisplayName() {
        return displayName;
    }
    
    public String getDescription() {
        return description;
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
}
