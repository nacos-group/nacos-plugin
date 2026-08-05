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

package com.alibaba.nacos.plugin.config;

import com.alibaba.nacos.api.plugin.ConfigItemDefinition;
import com.alibaba.nacos.api.plugin.ConfigItemEffectMode;
import com.alibaba.nacos.plugin.config.constants.ConfigChangeConstants;
import com.alibaba.nacos.plugin.config.constants.ConfigChangePointCutTypes;
import com.alibaba.nacos.plugin.config.model.ConfigChangeRequest;
import com.alibaba.nacos.plugin.config.model.ConfigChangeResponse;
import org.junit.Assert;
import org.junit.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

/**
 * WhiteListConfigChangePluginServiceTest.
 *
 * @author Nacos
 */
public class WhiteListConfigChangePluginServiceTest {

    @Test
    public void testConfigDefinitions() {
        WhiteListConfigChangePluginService service = new WhiteListConfigChangePluginService();

        Assert.assertTrue(service.isConfigurable());
        List<ConfigItemDefinition> definitions = service.getConfigDefinitions();
        Assert.assertEquals(1, definitions.size());
        ConfigItemDefinition suffixes = definitions.get(0);
        Assert.assertEquals("suffixes", suffixes.getKey());
        Assert.assertEquals("", suffixes.getDefaultValue());
        Assert.assertEquals(ConfigItemEffectMode.RUNTIME, suffixes.getEffectMode());
        Assert.assertTrue(suffixes.getAliases().contains("suffixs"));
        Assert.assertTrue(suffixes.getAliases()
                .contains("nacos.core.config.plugin.whitelist.suffixs"));
    }

    @Test
    public void testApplyConfigUsesDefensiveSnapshot() {
        WhiteListConfigChangePluginService service = new WhiteListConfigChangePluginService();
        Map<String, String> config = new LinkedHashMap<>();
        config.put("suffixes", "yaml");
        service.applyConfig(config);

        config.put("suffixes", "json");
        Map<String, String> currentConfig = service.getCurrentConfig();
        currentConfig.put("suffixes", "properties");

        Assert.assertEquals("yaml", service.getCurrentConfig().get("suffixes"));
    }

    @Test
    public void testExecuteUsesAppliedConfigSnapshot() throws Exception {
        WhiteListConfigChangePluginService service = new WhiteListConfigChangePluginService();
        service.applyConfig(newConfig("suffixes", "yaml"));
        MultipartFile sourceFile = createConfigExportFile();
        Object[] args = new Object[] {sourceFile};
        ConfigChangeRequest request = new ConfigChangeRequest(
                ConfigChangePointCutTypes.IMPORT_BY_HTTP);
        request.setArg(ConfigChangeConstants.ORIGINAL_ARGS, args);
        request.setArg(ConfigChangeConstants.PLUGIN_PROPERTIES,
                toProperties(service.getCurrentConfig()));
        ConfigChangeResponse response = new ConfigChangeResponse(
                ConfigChangePointCutTypes.IMPORT_BY_HTTP);

        service.execute(request, response);

        MultipartFile filteredFile = (MultipartFile) response.getArgs()[0];
        ZipUtils.UnZipResult unzipResult = ZipUtils.unzip(filteredFile.getBytes());
        Assert.assertEquals(1, unzipResult.getZipItemList().size());
        Assert.assertEquals("DEFAULT_GROUP/keep.yaml",
                unzipResult.getZipItemList().get(0).getItemName());
    }

    @Test
    public void testExecuteAcceptsLegacySuffixsProperty() throws Exception {
        WhiteListConfigChangePluginService service = new WhiteListConfigChangePluginService();
        MultipartFile sourceFile = createConfigExportFile();
        Object[] args = new Object[] {sourceFile};
        Properties properties = new Properties();
        properties.setProperty("suffixs", "json");
        ConfigChangeRequest request = new ConfigChangeRequest(
                ConfigChangePointCutTypes.IMPORT_BY_HTTP);
        request.setArg(ConfigChangeConstants.ORIGINAL_ARGS, args);
        request.setArg(ConfigChangeConstants.PLUGIN_PROPERTIES, properties);
        ConfigChangeResponse response = new ConfigChangeResponse(
                ConfigChangePointCutTypes.IMPORT_BY_HTTP);

        service.execute(request, response);

        MultipartFile filteredFile = (MultipartFile) response.getArgs()[0];
        ZipUtils.UnZipResult unzipResult = ZipUtils.unzip(filteredFile.getBytes());
        Assert.assertEquals(1, unzipResult.getZipItemList().size());
        Assert.assertEquals("DEFAULT_GROUP/drop.json",
                unzipResult.getZipItemList().get(0).getItemName());
    }

    private MultipartFile createConfigExportFile() {
        String metadata = "metadata:\n" + "  - dataId: keep.yaml\n" + "    group: DEFAULT_GROUP\n"
                + "    type: yaml\n" + "  - dataId: drop.json\n" + "    group: DEFAULT_GROUP\n"
                + "    type: json\n";
        List<ZipUtils.ZipItem> items = Arrays.asList(
                new ZipUtils.ZipItem(ZipUtils.CONFIG_EXPORT_METADATA_NEW, metadata),
                new ZipUtils.ZipItem("DEFAULT_GROUP/keep.yaml", "keep"),
                new ZipUtils.ZipItem("DEFAULT_GROUP/drop.json", "drop"));
        return new MockMultipartFile("file", "config.zip", "application/zip", ZipUtils.zip(items));
    }

    private Map<String, String> newConfig(String key, String value) {
        Map<String, String> config = new LinkedHashMap<>();
        config.put(key, value);
        return config;
    }

    private Properties toProperties(Map<String, String> config) {
        Properties properties = new Properties();
        properties.putAll(config);
        return properties;
    }
}
