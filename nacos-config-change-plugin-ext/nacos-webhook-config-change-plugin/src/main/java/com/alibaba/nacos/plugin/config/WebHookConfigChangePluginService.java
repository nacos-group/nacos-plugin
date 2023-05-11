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
import org.apache.http.HttpStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.SSLException;
import java.io.InterruptedIOException;
import java.net.ConnectException;
import java.net.UnknownHostException;
import java.util.Arrays;
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
    
    private final NacosRestTemplate restTemplate = HttpClientBeanHolder.getNacosRestTemplate(LOGGER);
    
    private final Set<Integer> retryResponseCodes = new CopyOnWriteArraySet<Integer>(
            Arrays.asList(HttpStatus.SC_INTERNAL_SERVER_ERROR, HttpStatus.SC_BAD_GATEWAY,
                    HttpStatus.SC_SERVICE_UNAVAILABLE, HttpStatus.SC_GATEWAY_TIMEOUT));
    
    private static final int INCREASE_STEPS = 1000;
    
    private static final int DEFAULT_MAX_CONTENT_CAPACITY = 10 * 1024;
    
    @Override
    public void execute(ConfigChangeRequest configChangeRequest, ConfigChangeResponse configChangeResponse) {
        final Properties properties = (Properties) configChangeRequest.getArg(ConfigChangeConstants.PLUGIN_PROPERTIES);
        final String webhookUrl = properties.getProperty("webhookUrl");
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
        final Object contentMaxCapacity = properties.getProperty("contentMaxCapacity");
        final String content = (String) configChangeRequest.getArg("content");
        int maxContent = DEFAULT_MAX_CONTENT_CAPACITY;
        if (contentMaxCapacity != null) {
            maxContent = Integer.parseInt((String) contentMaxCapacity);
        }
        // check content length
        if (content != null) {
            if (content.length() > maxContent) {
                configChangeNotifyInfo.setContent(content.substring(0, maxContent));
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
        configChangeNotifyInfo.setContent(content);
        return configChangeNotifyInfo;
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
