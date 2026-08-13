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

package com.alibaba.nacos.plugin.environment;

import com.alibaba.nacos.api.plugin.PluginInitializationPhase;
import com.alibaba.nacos.api.plugin.PluginType;
import com.alibaba.nacos.plugin.environment.spi.CustomEnvironmentPluginService;
import org.junit.Assert;
import org.junit.Test;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.ServiceLoader;

/**
 * NacosDbEncryptPluginServiceTest.
 *
 * @author Nacos
 */
public class NacosDbEncryptPluginServiceTest {

    private static final String DATASOURCE_DB_PWD_KEY = "nacos.plugin.datasource.db.password.0";

    private static final String LEGACY_DB_PWD_KEY = "db.password.0";

    @Test
    public void testEnvironmentPluginTypeUsesPreContextLifecycle() {
        Assert.assertEquals(PluginInitializationPhase.PRE_CONTEXT,
                PluginType.ENVIRONMENT.getInitializationPhase());
    }

    @Test
    public void testZeroConfigContract() {
        NacosDbEncryptPluginService service = new NacosDbEncryptPluginService();

        Assert.assertFalse(service.isConfigurable());
        Assert.assertTrue(service.getConfigDefinitions().isEmpty());
        Assert.assertTrue(service.getCurrentConfig().isEmpty());
        service.applyConfig(Collections.singletonMap("unused", "value"));
        Assert.assertTrue(service.getCurrentConfig().isEmpty());
    }

    @Test
    public void testPluginIdentityAndPropertyKeys() {
        NacosDbEncryptPluginService service = new NacosDbEncryptPluginService();

        Assert.assertEquals("NacosDbEncryptPluginService", service.pluginName());
        Assert.assertEquals(Integer.valueOf(1), service.order());
        Assert.assertEquals(new LinkedHashSet<>(Arrays.asList(DATASOURCE_DB_PWD_KEY, LEGACY_DB_PWD_KEY)),
                service.propertyKey());
    }

    @Test
    public void testCustomValueDecodesCanonicalDatabasePassword() {
        NacosDbEncryptPluginService service = new NacosDbEncryptPluginService();
        Map<String, Object> property = new HashMap<>();
        property.put(DATASOURCE_DB_PWD_KEY, encode("nacos-pass"));

        Map<String, Object> result = service.customValue(property);

        Assert.assertSame(property, result);
        Assert.assertEquals("nacos-pass", result.get(DATASOURCE_DB_PWD_KEY));
    }

    @Test
    public void testCustomValueDecodesLegacyDatabasePassword() {
        NacosDbEncryptPluginService service = new NacosDbEncryptPluginService();
        Map<String, Object> property = new HashMap<>();
        property.put(LEGACY_DB_PWD_KEY, encode("legacy-pass"));

        Map<String, Object> result = service.customValue(property);

        Assert.assertSame(property, result);
        Assert.assertEquals("legacy-pass", result.get(LEGACY_DB_PWD_KEY));
    }

    @Test
    public void testCustomValueDecodesBothCanonicalAndLegacyDatabasePasswords() {
        NacosDbEncryptPluginService service = new NacosDbEncryptPluginService();
        Map<String, Object> property = new HashMap<>();
        property.put(DATASOURCE_DB_PWD_KEY, encode("canonical-pass"));
        property.put(LEGACY_DB_PWD_KEY, encode("legacy-pass"));

        Map<String, Object> result = service.customValue(property);

        Assert.assertSame(property, result);
        Assert.assertEquals("canonical-pass", result.get(DATASOURCE_DB_PWD_KEY));
        Assert.assertEquals("legacy-pass", result.get(LEGACY_DB_PWD_KEY));
    }

    @Test
    public void testCustomValueSkipsNullDatabasePassword() {
        NacosDbEncryptPluginService service = new NacosDbEncryptPluginService();
        Map<String, Object> property = new HashMap<>();
        property.put(DATASOURCE_DB_PWD_KEY, null);
        property.put(LEGACY_DB_PWD_KEY, encode("legacy-pass"));

        Map<String, Object> result = service.customValue(property);

        Assert.assertSame(property, result);
        Assert.assertNull(result.get(DATASOURCE_DB_PWD_KEY));
        Assert.assertEquals("legacy-pass", result.get(LEGACY_DB_PWD_KEY));
    }

    @Test
    public void testServiceIsDiscoverableThroughSpiWithoutManualJoin() {
        boolean discovered = false;
        for (CustomEnvironmentPluginService service
                : ServiceLoader.load(CustomEnvironmentPluginService.class)) {
            if (service instanceof NacosDbEncryptPluginService) {
                discovered = true;
                break;
            }
        }

        Assert.assertTrue(discovered);
    }

    private String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }
}
