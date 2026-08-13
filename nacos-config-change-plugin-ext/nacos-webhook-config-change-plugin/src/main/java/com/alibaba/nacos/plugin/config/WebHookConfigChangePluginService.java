/*
 * Copyright 1999-2021 Alibaba Group Holding Ltd.
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

package com.alibaba.nacos.plugin.config;

import com.alibaba.nacos.api.plugin.ConfigItemDefinition;
import com.alibaba.nacos.api.plugin.ConfigItemEffectMode;
import com.alibaba.nacos.api.plugin.ConfigItemType;
import com.alibaba.nacos.common.http.HttpClientBeanHolder;
import com.alibaba.nacos.common.http.HttpRestResult;
import com.alibaba.nacos.common.http.client.NacosRestTemplate;
import com.alibaba.nacos.common.http.param.Header;
import com.alibaba.nacos.common.http.param.Query;
import com.alibaba.nacos.plugin.config.constants.ConfigChangeConstants;
import com.alibaba.nacos.plugin.config.constants.ConfigChangeExecuteTypes;
import com.alibaba.nacos.plugin.config.constants.ConfigChangePointCutTypes;
import com.alibaba.nacos.plugin.config.model.ConfigChangeRequest;
import com.alibaba.nacos.plugin.config.model.ConfigChangeResponse;
import com.alibaba.nacos.plugin.config.spi.ConfigChangePluginService;
import org.apache.hc.core5.http.HttpStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.SSLException;
import java.io.InterruptedIOException;
import java.net.ConnectException;
import java.net.UnknownHostException;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;
import java.util.concurrent.TimeUnit;

/**
 * WebHookConfigChangePluginService.
 *
 * @author liyunfei
 **/
public class WebHookConfigChangePluginService implements ConfigChangePluginService {
    
    private static final Logger LOGGER = LoggerFactory.getLogger(WebHookConfigChangePluginService.class);
    
    private static final String WEBHOOK_URL = "webhook-url";

    private static final String CONTENT_MAX_CAPACITY = "content-max-capacity";

    private static final String LEGACY_WEBHOOK_URL_CAMEL_CASE = "webhookUrl";

    private static final String LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE = "contentMaxCapacity";

    private static final String LEGACY_WEBHOOK_URL = "url";

    private static final String LEGACY_CONFIG_PREFIX = "nacos.core.config.plugin.webhook.";

    private static final List<ConfigItemDefinition> CONFIG_DEFINITIONS = buildConfigDefinitions();

    private final NacosRestTemplate restTemplate = HttpClientBeanHolder.getNacosRestTemplate(LOGGER);
    
    private final Set<Integer> retryResponseCodes = new CopyOnWriteArraySet<Integer>(
            Arrays.asList(HttpStatus.SC_INTERNAL_SERVER_ERROR, HttpStatus.SC_BAD_GATEWAY,
                    HttpStatus.SC_SERVICE_UNAVAILABLE, HttpStatus.SC_GATEWAY_TIMEOUT));
    
    private static final int INCREASE_STEPS = 1000;
    
    private static final int DEFAULT_MAX_CONTENT_CAPACITY = 10 * 1024;
    
    private volatile Map<String, String> currentConfig = Collections.emptyMap();

    private static List<ConfigItemDefinition> buildConfigDefinitions() {
        ConfigItemDefinition webhookUrl = new ConfigItemDefinition.Builder(WEBHOOK_URL,
                "Webhook URL", ConfigItemType.STRING)
                .description("Webhook endpoint used to notify config changes")
                .aliases(Arrays.asList(LEGACY_WEBHOOK_URL_CAMEL_CASE, LEGACY_WEBHOOK_URL,
                        LEGACY_CONFIG_PREFIX + LEGACY_WEBHOOK_URL_CAMEL_CASE,
                        LEGACY_CONFIG_PREFIX + LEGACY_WEBHOOK_URL))
                .effectMode(ConfigItemEffectMode.RUNTIME).build();
        ConfigItemDefinition contentMaxCapacity = new ConfigItemDefinition.Builder(
                CONTENT_MAX_CAPACITY, "Content max capacity", ConfigItemType.NUMBER)
                .description("Maximum content length in webhook payload")
                .defaultValue(String.valueOf(DEFAULT_MAX_CONTENT_CAPACITY))
                .aliases(Arrays.asList(LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE,
                        LEGACY_CONFIG_PREFIX + LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE))
                .effectMode(ConfigItemEffectMode.RUNTIME).build();
        return Collections.unmodifiableList(Arrays.asList(webhookUrl, contentMaxCapacity));
    }

    @Override
    public List<ConfigItemDefinition> getConfigDefinitions() {
        return CONFIG_DEFINITIONS;
    }

    @Override
    public void applyConfig(Map<String, String> config) {
        if (null == config) {
            currentConfig = Collections.emptyMap();
            return;
        }
        Map<String, String> normalizedConfig = new LinkedHashMap<>();
        String webhookUrl = getConfigValue(config, WEBHOOK_URL, LEGACY_WEBHOOK_URL_CAMEL_CASE,
                LEGACY_WEBHOOK_URL, LEGACY_CONFIG_PREFIX + LEGACY_WEBHOOK_URL_CAMEL_CASE,
                LEGACY_CONFIG_PREFIX + LEGACY_WEBHOOK_URL);
        if (webhookUrl != null) {
            normalizedConfig.put(WEBHOOK_URL, webhookUrl);
        }
        String contentMaxCapacity = getConfigValue(config, CONTENT_MAX_CAPACITY,
                LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE,
                LEGACY_CONFIG_PREFIX + LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE);
        if (contentMaxCapacity != null) {
            normalizedConfig.put(CONTENT_MAX_CAPACITY,
                    String.valueOf(parseContentMaxCapacity(contentMaxCapacity)));
        }
        currentConfig = normalizedConfig;
    }

    @Override
    public Map<String, String> getCurrentConfig() {
        return new LinkedHashMap<>(currentConfig);
    }

    @Override
    public void execute(ConfigChangeRequest configChangeRequest, ConfigChangeResponse configChangeResponse) {
        final Properties properties = (Properties) configChangeRequest.getArg(ConfigChangeConstants.PLUGIN_PROPERTIES);
        final String webhookUrl = getProperty(properties, WEBHOOK_URL, LEGACY_WEBHOOK_URL_CAMEL_CASE,
                LEGACY_WEBHOOK_URL, LEGACY_CONFIG_PREFIX + LEGACY_WEBHOOK_URL_CAMEL_CASE,
                LEGACY_CONFIG_PREFIX + LEGACY_WEBHOOK_URL);
        ConfigChangeNotifyInfo configChangeNotifyInfo = new ConfigChangeNotifyInfo(
                configChangeRequest.getRequestType().value(), true, (String) configChangeRequest.getArg("modifyTime"));
        wrapConfigChangeNotifyInfo(configChangeNotifyInfo, properties, configChangeRequest, configChangeResponse);
        ConfigChangePluginExecutor
                .executeAsyncConfigChangePluginTask(new WebhookNotifySingleTask(webhookUrl, configChangeNotifyInfo));
    }
    
    @Override
    public ConfigChangeExecuteTypes executeType() {
        return ConfigChangeExecuteTypes.EXECUTE_AFTER_TYPE;
    }
    
    @Override
    public String getServiceType() {
        return "webhook";
    }
    
    @Override
    public int getOrder() {
        return Integer.MAX_VALUE;
    }
    
    @Override
    public ConfigChangePointCutTypes[] pointcutMethodNames() {
        return ConfigChangePointCutTypes.values();
    }
    
    private ConfigChangeNotifyInfo wrapConfigChangeNotifyInfo(ConfigChangeNotifyInfo configChangeNotifyInfo,
            Properties properties, ConfigChangeRequest configChangeRequest, ConfigChangeResponse configChangeResponse) {
        final String contentMaxCapacity = getProperty(properties, CONTENT_MAX_CAPACITY,
                LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE,
                LEGACY_CONFIG_PREFIX + LEGACY_CONTENT_MAX_CAPACITY_CAMEL_CASE);
        final String content = (String) configChangeRequest.getArg("content");
        int maxContent = DEFAULT_MAX_CONTENT_CAPACITY;
        if (contentMaxCapacity != null) {
            maxContent = parseContentMaxCapacity(contentMaxCapacity);
        }
        // check content length
        if (content != null) {
            if (content.length() > maxContent) {
                configChangeNotifyInfo.setContent(content.substring(0, maxContent));
            } else {
                configChangeNotifyInfo.setContent(content);
            }
        }
        // only diliver err msg so far
        if (configChangeResponse.getMsg() != null) {
            configChangeNotifyInfo.setRs(false);
            configChangeNotifyInfo.setErrorMsg(configChangeResponse.getMsg());
        }
        if (configChangeRequest.getArg("dataId") != null) {
            configChangeNotifyInfo.setDataId((String) configChangeRequest.getArg("dataId"));
        }
        if (configChangeRequest.getArg("group") != null) {
            configChangeNotifyInfo.setGroup((String) configChangeRequest.getArg("group"));
        }
        if (configChangeRequest.getArg("tenant") != null) {
            configChangeNotifyInfo.setTenant((String) configChangeRequest.getArg("tenant"));
        }
        if (configChangeRequest.getArg("namespace") != null) {
            configChangeNotifyInfo.setNamespace((String) configChangeRequest.getArg("namespace"));
        }
        if (configChangeRequest.getArg("type") != null) {
            configChangeNotifyInfo.setType((String) configChangeRequest.getArg("type"));
        }
        if (configChangeRequest.getArg("tag") != null) {
            configChangeNotifyInfo.setTag((String) configChangeRequest.getArg("tag"));
        }
        if (configChangeRequest.getArg("configTags") != null) {
            configChangeNotifyInfo.setConfigTags((String) configChangeRequest.getArg("configTags"));
        }
        if (configChangeRequest.getArg("appName") != null) {
            configChangeNotifyInfo.setAppName((String) configChangeRequest.getArg("appName"));
        }
        if (configChangeRequest.getArg("use") != null) {
            configChangeNotifyInfo.setUse((String) configChangeRequest.getArg("use"));
        }
        if (configChangeRequest.getArg("srcUser") != null) {
            configChangeNotifyInfo.setSrcUser((String) configChangeRequest.getArg("srcUser"));
        }
        if (configChangeRequest.getArg("srcIp") != null) {
            configChangeNotifyInfo.setSrcIp((String) configChangeRequest.getArg("srcIp"));
        }
        if (configChangeRequest.getArg("effect") != null) {
            configChangeNotifyInfo.setEffect((String) configChangeRequest.getArg("effect"));
        }
        return configChangeNotifyInfo;
    }

    private static String getConfigValue(Map<String, String> config, String... keys) {
        for (String key : keys) {
            if (config.containsKey(key)) {
                return config.get(key);
            }
        }
        return null;
    }

    private static String getProperty(Properties properties, String... keys) {
        for (String key : keys) {
            String value = properties.getProperty(key);
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private static int parseContentMaxCapacity(String contentMaxCapacity) {
        String value = contentMaxCapacity.trim();
        if (value.length() == 0 || !value.matches("\\d+")) {
            throw new IllegalArgumentException("content-max-capacity must be a positive integer");
        }
        try {
            int maxContentCapacity = Integer.parseInt(value);
            if (maxContentCapacity <= 0) {
                throw new IllegalArgumentException("content-max-capacity must be a positive integer");
            }
            return maxContentCapacity;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("content-max-capacity exceeds supported integer range", e);
        }
    }
    
    private class WebhookNotifySingleTask implements Runnable {
        
        private String pushUrl;
        
        private ConfigChangeNotifyInfo configChangeNotifyInfo;
        
        private int retry = 0;
        
        private final int maxRetry = 6;
        
        public WebhookNotifySingleTask(String pushUrl, ConfigChangeNotifyInfo configChangeNotifyInfo) {
            this.pushUrl = pushUrl;
            this.configChangeNotifyInfo = configChangeNotifyInfo;
        }
        
        @Override
        public void run() {
            try {
                HttpRestResult<String> restResult = restTemplate
                        .post(pushUrl, Header.EMPTY, Query.EMPTY, configChangeNotifyInfo, String.class);
                int respCode = restResult.getCode();
                if (respCode != HttpStatus.SC_OK) {
                    if (!retryResponseCodes.contains(respCode)) {
                        LOGGER.warn(
                                "[{}]config change notify request failed,cause request params error,please check it",
                                getClass());
                    } else {
                        LOGGER.warn("config change notify request failed,will retry request {}",
                                restResult.getMessage());
                        retryRequest();
                    }
                }
            } catch (Exception e) {
                if (e instanceof InterruptedIOException || e instanceof UnknownHostException
                        || e instanceof ConnectException || e instanceof SSLException) {
                    LOGGER.warn("config change notify request failed,will retry request({}),cause: {}", retry,
                            e.getMessage());
                    retryRequest();
                } else {
                    LOGGER.warn("config change notify request failed,can not retry,case: {}", e.getMessage());
                }
            }
        }
        
        /**
         * Retry delay time.
         */
        private long getDelay() {
            return (long) retry * retry * INCREASE_STEPS;
        }
        
        private void retryRequest() {
            retry++;
            if (retry > maxRetry) {
                // Do not retry if over max retry count
                LOGGER.warn("retry to much,give up to push");
                return;
            }
            ConfigChangePluginExecutor.scheduleAsyncConfigChangePluginTask(this, getDelay(), TimeUnit.MILLISECONDS);
        }
    }
    
}
