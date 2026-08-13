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

import com.alibaba.nacos.api.exception.NacosException;
import com.alibaba.nacos.api.exception.api.NacosApiException;
import com.alibaba.nacos.api.model.v2.ErrorCode;
import com.alibaba.nacos.api.plugin.ConfigItemDefinition;
import com.alibaba.nacos.api.plugin.ConfigItemEffectMode;
import com.alibaba.nacos.api.plugin.ConfigItemType;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.AiResourceImportConstants;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportService;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportServiceBuilder;

import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Builder for authenticated skills.sh AI resource import service.
 *
 * @author elnafateh
 */
public class SkillsShImportServiceBuilder implements AiResourceImportServiceBuilder {
    
    /**
     * Keep a distinct managed source id from the built-in public skills.sh importer.
     */
    public static final String PLUGIN_NAME = "skills-sh-authenticated";
    
    /**
     * API metadata that identifies this implementation as the authenticated v1 protocol.
     */
    public static final String IMPORTER_TYPE = "skills-sh-v1";

    public static final String DEFAULT_ENDPOINT = "https://skills.sh";

    public static final String CONFIG_TOKEN = "token";

    public static final String CONFIG_CONNECT_TIMEOUT_MILLIS = "connect-timeout-ms";

    public static final String CONFIG_READ_TIMEOUT_MILLIS = "read-timeout-ms";

    private static final String DEFAULT_DISPLAY_NAME = "skills.sh Authenticated";

    private static final String DEFAULT_DESCRIPTION =
            "Import Skills from authenticated skills.sh v1 APIs.";

    private static final int DEFAULT_CONNECT_TIMEOUT_MILLIS = 3000;

    private static final int DEFAULT_READ_TIMEOUT_MILLIS = 10000;

    /**
     * Legacy skills.sh importer configuration prefix.
     *
     * @deprecated use {@code nacos.plugin.ai-resource-import.skills-sh-authenticated.} instead.
     */
    @Deprecated
    private static final String LEGACY_PREFIX = "nacos.plugin.ai.importer.skills.skills-sh.";

    /*
     * In the 3.3 SPI, source-owned settings are declared by the builder instead of the
     * removed AiResourceImportSourceProvider. Token is marked sensitive so config query
     * APIs can mask it.
     */
    private final List<ConfigItemDefinition> definitions = Collections.unmodifiableList(
            Arrays.asList(
                    definition(AiResourceImportConstants.CONFIG_ENDPOINT, "Source endpoint",
                            ConfigItemType.STRING, DEFAULT_ENDPOINT,
                            "skills.sh endpoint that exposes /api/v1/skills APIs.",
                            ConfigItemEffectMode.RESTART,
                            aliases(AiResourceImportConstants.CONFIG_ENDPOINT, "url")),
                    definition(CONFIG_TOKEN, "Bearer token", ConfigItemType.STRING, "",
                            "Bearer token for authenticated skills.sh v1 API requests.",
                            ConfigItemEffectMode.RUNTIME,
                            aliases(CONFIG_TOKEN, "auth-token", "authToken"), true),
                    definition(AiResourceImportConstants.CONFIG_ALLOW_HTTP, "Allow HTTP",
                            ConfigItemType.BOOLEAN, Boolean.FALSE.toString(),
                            "Allow non-HTTPS requests to the configured endpoint.",
                            ConfigItemEffectMode.RESTART,
                            aliases(AiResourceImportConstants.CONFIG_ALLOW_HTTP, "allowHttp")),
                    definition(AiResourceImportConstants.CONFIG_ALLOW_PRIVATE_NETWORK,
                            "Allow private network", ConfigItemType.BOOLEAN,
                            Boolean.FALSE.toString(),
                            "Allow requests to local and private network addresses.",
                            ConfigItemEffectMode.RESTART,
                            aliases(AiResourceImportConstants.CONFIG_ALLOW_PRIVATE_NETWORK,
                                    "allowPrivateNetwork")),
                    definition(AiResourceImportConstants.CONFIG_DISPLAY_NAME, "Display name",
                            ConfigItemType.STRING, DEFAULT_DISPLAY_NAME,
                            "Display name returned by the import source API.",
                            ConfigItemEffectMode.RUNTIME,
                            aliases(AiResourceImportConstants.CONFIG_DISPLAY_NAME,
                                    "displayName")),
                    definition(AiResourceImportConstants.CONFIG_DESCRIPTION, "Description",
                            ConfigItemType.STRING, DEFAULT_DESCRIPTION,
                            "Description returned by the import source API.",
                            ConfigItemEffectMode.RUNTIME,
                            aliases(AiResourceImportConstants.CONFIG_DESCRIPTION)),
                    definition(CONFIG_CONNECT_TIMEOUT_MILLIS, "Connect timeout",
                            ConfigItemType.NUMBER,
                            Integer.toString(DEFAULT_CONNECT_TIMEOUT_MILLIS),
                            "HTTP connect timeout in milliseconds.",
                            ConfigItemEffectMode.RUNTIME,
                            aliases(CONFIG_CONNECT_TIMEOUT_MILLIS)),
                    definition(CONFIG_READ_TIMEOUT_MILLIS, "Read timeout",
                            ConfigItemType.NUMBER, Integer.toString(DEFAULT_READ_TIMEOUT_MILLIS),
                            "HTTP read timeout in milliseconds.",
                            ConfigItemEffectMode.RUNTIME, aliases(CONFIG_READ_TIMEOUT_MILLIS)),
                    definition(AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT,
                            "Maximum item count", ConfigItemType.NUMBER,
                            Integer.toString(AiResourceImportConstants.DEFAULT_MAX_ITEM_COUNT),
                            "Maximum number of candidates or files processed by one import request.",
                            ConfigItemEffectMode.RUNTIME,
                            aliases(AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT)),
                    definition(AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE,
                            "Maximum artifact size", ConfigItemType.NUMBER,
                            Long.toString(AiResourceImportConstants.DEFAULT_MAX_ARTIFACT_SIZE),
                            "Maximum accepted artifact size in bytes.",
                            ConfigItemEffectMode.RUNTIME,
                            aliases(AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE))));

    private volatile SkillsShImportConfig snapshot =
            parseConfig(Collections.<String, String>emptyMap());

    private volatile boolean initialized;

    @Override
    public String pluginName() {
        return PLUGIN_NAME;
    }

    @Override
    public String importerType() {
        return IMPORTER_TYPE;
    }

    @Override
    public String displayName() {
        return snapshot.getDisplayName();
    }

    @Override
    public String description() {
        return snapshot.getDescription();
    }

    @Override
    public Set<String> supportedResourceTypes() {
        return Collections.unmodifiableSet(new LinkedHashSet<String>(
                Collections.singleton(AiResourceImportConstants.RESOURCE_TYPE_SKILL)));
    }

    @Override
    public List<ConfigItemDefinition> getConfigDefinitions() {
        return definitions;
    }

    @Override
    public synchronized void applyConfig(Map<String, String> config) {
        /*
         * Replace the whole snapshot atomically. Each request-scoped service built later
         * receives one immutable view of endpoint, auth, network policy, and limits.
         */
        snapshot = parseConfig(config == null ? Collections.<String, String>emptyMap() : config);
        initialized = true;
    }

    @Override
    public Map<String, String> getCurrentConfig() {
        return snapshot.getValues();
    }

    @Override
    public AiResourceImportService build() throws NacosException {
        if (!initialized) {
            throw invalid("AI resource import plugin has not been initialized: " + PLUGIN_NAME);
        }
        SkillsShImportConfig config = snapshot;
        validateEndpoint(config);
        /*
         * Request context no longer carries AiResourceImportSource in 3.3, so inject the
         * resolved builder snapshot directly into the request-scoped service.
         */
        return new SkillsShImportService(config);
    }

    private SkillsShImportConfig parseConfig(Map<String, String> config) {
        String endpoint = value(config, AiResourceImportConstants.CONFIG_ENDPOINT,
                DEFAULT_ENDPOINT);
        String token = value(config, CONFIG_TOKEN, "");
        boolean allowHttp = Boolean.parseBoolean(value(config,
                AiResourceImportConstants.CONFIG_ALLOW_HTTP, Boolean.FALSE.toString()));
        boolean allowPrivateNetwork = Boolean.parseBoolean(value(config,
                AiResourceImportConstants.CONFIG_ALLOW_PRIVATE_NETWORK,
                Boolean.FALSE.toString()));
        String displayName = value(config, AiResourceImportConstants.CONFIG_DISPLAY_NAME,
                DEFAULT_DISPLAY_NAME);
        String description = value(config, AiResourceImportConstants.CONFIG_DESCRIPTION,
                DEFAULT_DESCRIPTION);
        int connectTimeoutMillis = positiveInt(value(config, CONFIG_CONNECT_TIMEOUT_MILLIS,
                Integer.toString(DEFAULT_CONNECT_TIMEOUT_MILLIS)),
                CONFIG_CONNECT_TIMEOUT_MILLIS);
        int readTimeoutMillis = positiveInt(value(config, CONFIG_READ_TIMEOUT_MILLIS,
                Integer.toString(DEFAULT_READ_TIMEOUT_MILLIS)), CONFIG_READ_TIMEOUT_MILLIS);
        int maxItemCount = positiveInt(value(config,
                AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT,
                Integer.toString(AiResourceImportConstants.DEFAULT_MAX_ITEM_COUNT)),
                AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT);
        long maxArtifactSize = positiveLong(value(config,
                AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE,
                Long.toString(AiResourceImportConstants.DEFAULT_MAX_ARTIFACT_SIZE)),
                AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE);
        Map<String, String> values = new LinkedHashMap<String, String>();
        values.put(AiResourceImportConstants.CONFIG_ENDPOINT, endpoint);
        values.put(CONFIG_TOKEN, token);
        values.put(AiResourceImportConstants.CONFIG_ALLOW_HTTP, Boolean.toString(allowHttp));
        values.put(AiResourceImportConstants.CONFIG_ALLOW_PRIVATE_NETWORK,
                Boolean.toString(allowPrivateNetwork));
        values.put(AiResourceImportConstants.CONFIG_DISPLAY_NAME, displayName);
        values.put(AiResourceImportConstants.CONFIG_DESCRIPTION, description);
        values.put(CONFIG_CONNECT_TIMEOUT_MILLIS, Integer.toString(connectTimeoutMillis));
        values.put(CONFIG_READ_TIMEOUT_MILLIS, Integer.toString(readTimeoutMillis));
        values.put(AiResourceImportConstants.CONFIG_MAX_ITEM_COUNT,
                Integer.toString(maxItemCount));
        values.put(AiResourceImportConstants.CONFIG_MAX_ARTIFACT_SIZE,
                Long.toString(maxArtifactSize));
        return new SkillsShImportConfig(values, endpoint, token, allowHttp, allowPrivateNetwork,
                displayName, description, connectTimeoutMillis, readTimeoutMillis, maxItemCount,
                maxArtifactSize);
    }

    private String value(Map<String, String> config, String key, String defaultValue) {
        String result = config.get(key);
        return result == null ? defaultValue : result.trim();
    }

    private int positiveInt(String value, String key) {
        int result = Integer.parseInt(value);
        if (result <= 0) {
            throw new IllegalArgumentException(key + " must be greater than 0.");
        }
        return result;
    }

    private long positiveLong(String value, String key) {
        long result = Long.parseLong(value);
        if (result <= 0) {
            throw new IllegalArgumentException(key + " must be greater than 0.");
        }
        return result;
    }

    private void validateEndpoint(SkillsShImportConfig config) throws NacosException {
        if (StringUtils.isBlank(config.getEndpoint())) {
            throw invalid("AI resource import plugin endpoint is missing: " + PLUGIN_NAME);
        }
        try {
            URI endpoint = URI.create(config.getEndpoint());
            if (!endpoint.isAbsolute() || StringUtils.isBlank(endpoint.getHost())) {
                throw invalid("AI resource import plugin endpoint is invalid: " + PLUGIN_NAME);
            }
        } catch (IllegalArgumentException e) {
            throw invalid("AI resource import plugin endpoint is invalid: " + PLUGIN_NAME);
        }
    }

    private static ConfigItemDefinition definition(String key, String name, ConfigItemType type,
            String defaultValue, String description, ConfigItemEffectMode effectMode,
            List<String> aliases) {
        return definition(key, name, type, defaultValue, description, effectMode, aliases, false);
    }

    private static ConfigItemDefinition definition(String key, String name, ConfigItemType type,
            String defaultValue, String description, ConfigItemEffectMode effectMode,
            List<String> aliases, boolean sensitive) {
        return new ConfigItemDefinition.Builder(key, name, type).defaultValue(defaultValue)
                .description(description).effectMode(effectMode).aliases(aliases)
                .sensitive(sensitive).build();
    }

    private static List<String> aliases(String... itemKeys) {
        List<String> result = new ArrayList<String>();
        for (String each : itemKeys) {
            result.add(LEGACY_PREFIX + each);
        }
        return result;
    }

    private NacosException invalid(String message) {
        return new NacosApiException(NacosException.INVALID_PARAM,
                ErrorCode.PARAMETER_VALIDATE_ERROR, message);
    }
}
