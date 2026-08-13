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
import com.alibaba.nacos.plugin.config.constants.ConfigChangeConstants;
import com.alibaba.nacos.plugin.config.constants.ConfigChangePointCutTypes;
import com.alibaba.nacos.plugin.config.model.ConfigChangeRequest;
import com.alibaba.nacos.plugin.config.model.ConfigChangeResponse;
import org.junit.Assert;
import org.junit.Test;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

/**
 * @author liyunfei
 **/
public class WebHookConfigChangePluginServiceTest {
    
    private static final int CONTENT_MAX_CAPACITY = 10 * 1024;
    
    private static final String WEBHOOK_URL = "http://localhost:8080/webhook/send?token=***";
    
    @Test
    public void testConfigDefinitions() {
        final WebHookConfigChangePluginService webHookConfigChangePluginService =
                new WebHookConfigChangePluginService();

        Assert.assertTrue(webHookConfigChangePluginService.isConfigurable());
        List<ConfigItemDefinition> definitions =
                webHookConfigChangePluginService.getConfigDefinitions();
        Assert.assertEquals(2, definitions.size());
        ConfigItemDefinition webhookUrl = definitions.get(0);
        Assert.assertEquals("webhook-url", webhookUrl.getKey());
        Assert.assertEquals(ConfigItemEffectMode.RUNTIME, webhookUrl.getEffectMode());
        Assert.assertTrue(webhookUrl.getAliases().contains("webhookUrl"));
        Assert.assertTrue(webhookUrl.getAliases().contains("url"));
        Assert.assertTrue(webhookUrl.getAliases()
                .contains("nacos.core.config.plugin.webhook.webhookUrl"));
        Assert.assertTrue(webhookUrl.getAliases()
                .contains("nacos.core.config.plugin.webhook.url"));
        ConfigItemDefinition contentMaxCapacity = definitions.get(1);
        Assert.assertEquals("content-max-capacity", contentMaxCapacity.getKey());
        Assert.assertEquals(String.valueOf(CONTENT_MAX_CAPACITY),
                contentMaxCapacity.getDefaultValue());
        Assert.assertTrue(contentMaxCapacity.getAliases().contains("contentMaxCapacity"));
        Assert.assertTrue(contentMaxCapacity.getAliases()
                .contains("nacos.core.config.plugin.webhook.contentMaxCapacity"));
        Assert.assertEquals(ConfigItemEffectMode.RUNTIME, contentMaxCapacity.getEffectMode());
    }

    @Test
    public void testApplyConfigUsesDefensiveSnapshot() {
        final WebHookConfigChangePluginService webHookConfigChangePluginService =
                new WebHookConfigChangePluginService();
        Map<String, String> config = new LinkedHashMap<>();
        config.put("webhook-url", WEBHOOK_URL);
        config.put("content-max-capacity", String.valueOf(CONTENT_MAX_CAPACITY));
        webHookConfigChangePluginService.applyConfig(config);

        config.put("webhook-url", "http://localhost:8080/changed");
        Map<String, String> currentConfig = webHookConfigChangePluginService.getCurrentConfig();
        currentConfig.put("webhook-url", "http://localhost:8080/mutated");

        Assert.assertEquals(WEBHOOK_URL,
                webHookConfigChangePluginService.getCurrentConfig().get("webhook-url"));
    }

    @Test
    public void testApplyConfigAcceptsLegacyAliases() {
        final WebHookConfigChangePluginService webHookConfigChangePluginService =
                new WebHookConfigChangePluginService();
        Map<String, String> config = new LinkedHashMap<>();
        config.put("webhookUrl", WEBHOOK_URL);
        config.put("nacos.core.config.plugin.webhook.contentMaxCapacity",
                String.valueOf(CONTENT_MAX_CAPACITY));

        webHookConfigChangePluginService.applyConfig(config);

        Assert.assertEquals(WEBHOOK_URL,
                webHookConfigChangePluginService.getCurrentConfig().get("webhook-url"));
        Assert.assertEquals(String.valueOf(CONTENT_MAX_CAPACITY),
                webHookConfigChangePluginService.getCurrentConfig().get("content-max-capacity"));
    }

    @Test
    public void testApplyConfigRejectsDecimalContentMaxCapacity() {
        assertInvalidContentMaxCapacity("1.5");
    }

    @Test
    public void testApplyConfigRejectsNonPositiveContentMaxCapacity() {
        assertInvalidContentMaxCapacity("0");
        assertInvalidContentMaxCapacity("-1");
    }

    @Test
    public void testApplyConfigRejectsOverflowContentMaxCapacity() {
        assertInvalidContentMaxCapacity("2147483648");
    }

    @Test
    public void testExecute() {
        final WebHookConfigChangePluginService webHookConfigChangePluginService =
                new WebHookConfigChangePluginService();
        final ConfigChangePointCutTypes pointCutType = ConfigChangePointCutTypes.PUBLISH_BY_HTTP;
        final String dataId = "test-dev.yaml";
        final String group = "DEFAULT_GROUP";
        final String content = "ok";
        Properties properties = new Properties();
        ConfigChangeResponse configChangeResponse = new ConfigChangeResponse(
                ConfigChangePointCutTypes.PUBLISH_BY_HTTP);
        ConfigChangeRequest configChangeRequest = new ConfigChangeRequest(pointCutType);
        webHookConfigChangePluginService.applyConfig(newConfig("content-max-capacity",
                String.valueOf(CONTENT_MAX_CAPACITY), "webhook-url", WEBHOOK_URL));
        properties.putAll(webHookConfigChangePluginService.getCurrentConfig());
        configChangeRequest.setArg(ConfigChangeConstants.PLUGIN_PROPERTIES, properties);
        configChangeRequest.setArg("content", content);
        configChangeRequest.setArg("dataId", dataId);
        configChangeRequest.setArg("group", group);
        webHookConfigChangePluginService.execute(configChangeRequest, configChangeResponse);
        configChangeResponse.setMsg("FileFormatPlugin validate is not pass");
        configChangeResponse.setSuccess(false);
        webHookConfigChangePluginService.execute(configChangeRequest, configChangeResponse);
    }

    private void assertInvalidContentMaxCapacity(String contentMaxCapacity) {
        try {
            new WebHookConfigChangePluginService().applyConfig(newConfig(
                    "content-max-capacity", contentMaxCapacity));
            Assert.fail("Expected IllegalArgumentException");
        } catch (IllegalArgumentException ignored) {
        }
    }

    private Map<String, String> newConfig(String... keysAndValues) {
        Map<String, String> config = new LinkedHashMap<>();
        for (int i = 0; i < keysAndValues.length; i += 2) {
            config.put(keysAndValues[i], keysAndValues[i + 1]);
        }
        return config;
    }
}
