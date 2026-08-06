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
import org.junit.Assert;
import org.junit.Test;

import java.util.Collections;
import java.util.ServiceLoader;

/**
 * OceanbaseDatabaseDialectTest.
 *
 * @author Nacos
 */
public class OceanbaseDatabaseDialectTest {
    
    private static final String OCEANBASE = "oceanbase";
    
    @Test
    public void testZeroConfigContract() {
        DatabaseDialect dialect = new OceanbaseDatabaseDialect();
        PluginConfigSpec configSpec = (PluginConfigSpec) dialect;
        
        Assert.assertEquals(OCEANBASE, dialect.getType());
        Assert.assertFalse(configSpec.isConfigurable());
        Assert.assertTrue(configSpec.getConfigDefinitions().isEmpty());
        Assert.assertTrue(configSpec.getCurrentConfig().isEmpty());
        configSpec.applyConfig(Collections.singletonMap("unused", "value"));
        Assert.assertTrue(configSpec.getCurrentConfig().isEmpty());
    }
    
    @Test
    public void testDiscoverableThroughSpi() {
        Assert.assertTrue(isDiscoverable(OCEANBASE));
    }
    
    private boolean isDiscoverable(String type) {
        for (DatabaseDialect dialect : ServiceLoader.load(DatabaseDialect.class)) {
            if (type.equals(dialect.getType()) && dialect instanceof OceanbaseDatabaseDialect) {
                return true;
            }
        }
        return false;
    }
}
