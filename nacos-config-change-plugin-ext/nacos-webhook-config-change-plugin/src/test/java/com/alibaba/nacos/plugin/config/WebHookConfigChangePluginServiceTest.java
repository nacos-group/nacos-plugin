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

import com.alibaba.nacos.plugin.config.constants.ConfigChangeConstants;
import com.alibaba.nacos.plugin.config.constants.ConfigChangePointCutTypes;
import com.alibaba.nacos.plugin.config.model.ConfigChangeRequest;
import com.alibaba.nacos.plugin.config.model.ConfigChangeResponse;
import org.junit.Test;

import java.util.Properties;

/**
 * @author liyunfei
 **/
public class WebHookConfigChangePluginServiceTest {
    
    private static final int CONTENT_MAX_CAPACITY = 10 * 1024;
    
    private static final String WEBHOOK_URL = "http://localhost:8080/webhook/send?token=***";
    
    @Test
    public void testExecute() {
        final WebHookConfigChangePluginService webHookConfigChangePluginService = new WebHookConfigChangePluginService();
        final ConfigChangePointCutTypes pointCutType = ConfigChangePointCutTypes.PUBLISH_BY_HTTP;
        final String dataId = "test-dev.yaml";
        final String group = "DEFAULT_GROUP";
        final String content = "ok";
        Properties properties = new Properties();
        ConfigChangeResponse configChangeResponse = new ConfigChangeResponse(ConfigChangePointCutTypes.PUBLISH_BY_HTTP);
        ConfigChangeRequest configChangeRequest = new ConfigChangeRequest(pointCutType);
        properties.setProperty("contentMaxCapacity", String.valueOf(CONTENT_MAX_CAPACITY));
        properties.setProperty("webhookUrl", WEBHOOK_URL);
        configChangeRequest.setArg(ConfigChangeConstants.PLUGIN_PROPERTIES, properties);
        configChangeRequest.setArg("content", content);
        configChangeRequest.setArg("dataId", dataId);
        configChangeRequest.setArg("group", group);
        webHookConfigChangePluginService.execute(configChangeRequest, configChangeResponse);
        configChangeResponse.setMsg("FileFormatPlugin validate is not pass");
        configChangeResponse.setSuccess(false);
        webHookConfigChangePluginService.execute(configChangeRequest, configChangeResponse);
    }
}
