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

package com.alibaba.nacos.plugin.datasource.dialect;

import com.alibaba.nacos.api.plugin.PluginConfigSpec;
import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.mapper.Mapper;
import org.junit.Assert;
import org.junit.Test;

import java.util.Collections;
import java.util.ServiceLoader;

/**
 * XuguDatabaseDialectTest.
 *
 * @author Nacos
 */
public class XuguDatabaseDialectTest {

    @Test
    public void testZeroConfigContract() {
        DatabaseDialect dialect = new XuguDatabaseDialect();

        PluginConfigSpec configSpec = (PluginConfigSpec) dialect;
        Assert.assertEquals(DatabaseTypeConstant.XUGU, dialect.getType());
        Assert.assertFalse(configSpec.isConfigurable());
        Assert.assertTrue(configSpec.getConfigDefinitions().isEmpty());
        Assert.assertTrue(configSpec.getCurrentConfig().isEmpty());
        configSpec.applyConfig(Collections.singletonMap("unused", "value"));
        Assert.assertTrue(configSpec.getCurrentConfig().isEmpty());
    }

    @Test
    public void testDiscoverableThroughSpi() {
        Assert.assertTrue(isDiscoverable(DatabaseTypeConstant.XUGU));
    }

    @Test
    public void testMapperSpiDoesNotReferenceRemovedMappers() {
        int mapperCount = 0;
        for (Mapper mapper : ServiceLoader.load(Mapper.class)) {
            String className = mapper.getClass().getName();
            Assert.assertFalse(className, className.contains("ConfigInfoBetaMapper"));
            Assert.assertFalse(className, className.contains("ConfigInfoTagMapper"));
            Assert.assertFalse(className, className.contains("ConfigMigrateMapper"));
            mapperCount++;
        }
        Assert.assertTrue(mapperCount > 0);
    }

    private boolean isDiscoverable(String type) {
        for (DatabaseDialect dialect : ServiceLoader.load(DatabaseDialect.class)) {
            if (type.equals(dialect.getType()) && dialect instanceof XuguDatabaseDialect) {
                return true;
            }
        }
        return false;
    }
}
