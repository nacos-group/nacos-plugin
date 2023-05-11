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

import org.junit.Assert;
import org.junit.Test;

/**
 * FileFormatConfigChangePluginServiceTest.
 *
 * @author liyunfei
 **/
public class FileFormatConfigChangePluginServiceTest {

    private String textContent = "text123";

    private String jsonContent = "{\"hello\":\"hello\"}";

    private String propertiesContent = "# webhook\n" +
            "nacos.core.config.plugin.webhook.enabled=true\n" +
            "# It is recommended to use EB https://help.aliyun.com/document_detail/413974.html\n" +
            "nacos.core.config.plugin.webhook.url=http://localhost:8080/webhook/send\n" +
            "  # http://***.aliyuncs.com/webhook/putEvents?token=***\n" +
            "nacos.core.config.plugin.webhook.contentMaxCapacity=102400\n" +
            "# whitelist\n" +
            "nacos.core.config.plugin.whitelist.enabled=true\n" +
            "nacos.core.config.plugin.whitelist.suffixs=xml,text,properties,yaml,html\n" +
            "# fileformatcheck,which validate the import file of type and content\n" +
            "nacos.core.config.plugin.fileformatcheck.enabled=true";

    private String xmlContent = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
            "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"\n" +
            "         xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n" +
            "         xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd\">\n" +
            "    <parent>\n" +
            "        <artifactId>nacos-plugin-ext</artifactId>\n" +
            "        <groupId>com.alibaba.nacos</groupId>\n" +
            "        <version>${revision}</version>\n" +
            "    </parent>\n" +
            "    <modelVersion>4.0.0</modelVersion>\n" +
            "\n" +
            "    <artifactId>nacos-config-change-plugin-ext</artifactId>\n" +
            "    <packaging>pom</packaging>\n" +
            "\n" +
            "    <modules>\n" +
            "        <module>nacos-whitelist-config-change-plugin</module>\n" +
            "        <module>nacos-fileformat-config-change-plugin</module>\n" +
            "        <module>nacos-webhook-config-change-plugin</module>\n" +
            "    </modules>\n" +
            "\n" +
            "    <properties>\n" +
            "        <yaml.version>1.29</yaml.version>\n" +
            "    </properties>\n" +
            "\n" +
            "    <dependencies>\n" +
            "        <dependency>\n" +
            "            <groupId>com.alibaba.nacos</groupId>\n" +
            "            <artifactId>nacos-config-plugin</artifactId>\n" +
            "            <version>${alibaba-nacos.version}</version>\n" +
            "        </dependency>\n" +
            "        <dependency>\n" +
            "            <groupId>com.alibaba.nacos</groupId>\n" +
            "            <artifactId>nacos-common</artifactId>\n" +
            "        </dependency>\n" +
            "        <dependency>\n" +
            "            <groupId>org.yaml</groupId>\n" +
            "            <artifactId>snakeyaml</artifactId>\n" +
            "            <version>${yaml.version}</version>\n" +
            "            <scope>provided</scope>\n" +
            "        </dependency>\n" +
            "    </dependencies>\n" +
            "\n" +
            "</project>";

    private String htmlContent = "<!DOCTYPE html>\n" +
            "<html>\n" +
            "<head>\n" +
            "    <meta charset=\"UTF-8\">\n" +
            "    <title>登录</title>\n" +
            "</head>\n" +
            "<body>\n" +
            "<h3>登录</h3>\n" +
            "<form action=\"/nacos/login\" method=\"post\">\n" +
            "    <table>\n" +
            "        <tr>\n" +
            "            <td>用户名:</td>\n" +
            "            <td><input type=\"text\" name=\"username\"></td>\n" +
            "        </tr>\n" +
            "        <tr>\n" +
            "            <td>密码:</td>\n" +
            "            <td><input type=\"password\" name=\"password\"></td>\n" +
            "        </tr>\n" +
            "        <tr>\n" +
            "            <td colspan=\"2\">\n" +
            "                <button type=\"submit\">登录</button>\n" +
            "            </td>\n" +
            "        </tr>\n" +
            "    </table>\n" +
            "</form>\n" +
            "</body>\n" +
            "</html>\n";

    private String yamlContent = "hello: hello";

    @Test
    public void testValidateText() {
        String type = "text";
        boolean rs = FileFormatConfigChangePluginService.validate(textContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(jsonContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(xmlContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(propertiesContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(yamlContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(htmlContent, type);
        Assert.assertTrue(rs);
    }

    @Test
    public void testValidateJson() {
        String type = "json";
        boolean rs = FileFormatConfigChangePluginService.validate(jsonContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(xmlContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(propertiesContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(textContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(htmlContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(yamlContent, type);
        Assert.assertFalse(rs);
    }

    @Test
    public void testValidateXml() {
        String type = "xml";
        boolean rs = FileFormatConfigChangePluginService.validate(xmlContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(jsonContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(propertiesContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(textContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(htmlContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(yamlContent, type);
        Assert.assertFalse(rs);
    }

    @Test
    public void testValidateHtml() {
        String type = "html";
        boolean rs = FileFormatConfigChangePluginService.validate(htmlContent, type);
        Assert.assertTrue(rs);
        rs = FileFormatConfigChangePluginService.validate(jsonContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(propertiesContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(textContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(yamlContent, type);
        Assert.assertFalse(rs);
        rs = FileFormatConfigChangePluginService.validate(xmlContent, type);
        Assert.assertTrue(rs);
    }

    @Test
    public void testValidateProperties() {
        String type = "properties";
        boolean rs = FileFormatConfigChangePluginService.validate(propertiesContent, type);
        Assert.assertTrue(rs);
    }
}
