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

package com.alibaba.nacos.plugin.environment;

import com.alibaba.nacos.api.plugin.ConfigItemDefinition;
import com.alibaba.nacos.api.plugin.PluginConfigSpec;
import com.alibaba.nacos.plugin.environment.spi.CustomEnvironmentPluginService;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Nacos Db password encrypt plugin service implementation.
 *
 * @author huangtianhui
 */
@SuppressWarnings("PMD.ServiceOrDaoClassShouldEndWithImplRule")
public class NacosDbEncryptPluginService
        implements CustomEnvironmentPluginService, PluginConfigSpec {

    private static final String DATASOURCE_DB_PWD_KEY = "nacos.plugin.datasource.db.password.0";

    private static final String LEGACY_DB_PWD_KEY = "db.password.0";

    private static final Set<String> PROPERTY_KEYS = Collections.unmodifiableSet(
            new LinkedHashSet<>(Arrays.asList(DATASOURCE_DB_PWD_KEY, LEGACY_DB_PWD_KEY)));

    @Override
    public Map<String, Object> customValue(Map<String, Object> property) {
        decodePassword(property, DATASOURCE_DB_PWD_KEY);
        decodePassword(property, LEGACY_DB_PWD_KEY);
        return property;
    }

    @Override
    public Set<String> propertyKey() {
        return PROPERTY_KEYS;
    }

    @Override
    public Integer order() {
        return 1;
    }

    @Override
    public String pluginName() {
        return "NacosDbEncryptPluginService";
    }

    @Override
    public List<ConfigItemDefinition> getConfigDefinitions() {
        return Collections.emptyList();
    }

    private void decodePassword(Map<String, Object> property, String key) {
        Object password = property.get(key);
        if (password == null) {
            return;
        }
        byte[] decode = Base64.getDecoder().decode((String) password);
        property.put(key, new String(decode, StandardCharsets.UTF_8));
    }
}
