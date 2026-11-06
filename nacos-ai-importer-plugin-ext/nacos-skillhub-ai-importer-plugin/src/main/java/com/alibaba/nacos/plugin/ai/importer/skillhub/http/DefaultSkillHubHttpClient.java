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
package com.alibaba.nacos.plugin.ai.importer.skillhub.http;

import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.skillhub.SkillHubImportConfig;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.Locale;

/**
 * Default URLConnection-based SkillHub HTTP client.
 *
 * @author nacos
 */
public class DefaultSkillHubHttpClient implements SkillHubHttpClient {
    
    private static final String HTTPS = "https";
    
    @Override
    public SkillHubHttpResponse get(SkillHubImportConfig config, String url, boolean followRedirects,
            String hostHeader, boolean withAuth) throws Exception {
        URL target = new URL(url);
        validateTarget(config, target);
        HttpURLConnection connection = (HttpURLConnection) target.openConnection();
        connection.setRequestMethod("GET");
        connection.setConnectTimeout(config.getConnectTimeoutMillis());
        connection.setReadTimeout(config.getReadTimeoutMillis());
        connection.setInstanceFollowRedirects(followRedirects);
        connection.setRequestProperty("Accept", "*/*");
        if (StringUtils.isNotBlank(hostHeader)) {
            connection.setRequestProperty("Host", hostHeader.trim());
        }
        if (withAuth) {
            String token = config.getToken();
            if (StringUtils.isNotBlank(token)) {
                connection.setRequestProperty("Authorization", "Bearer " + token.trim());
            }
        }
        int statusCode = connection.getResponseCode();
        String location = connection.getHeaderField("Location");
        InputStream stream = statusCode >= 400 ? connection.getErrorStream() : connection.getInputStream();
        byte[] body = readBody(stream);
        connection.disconnect();
        return new SkillHubHttpResponse(url, statusCode, body, location);
    }
    
    private void validateTarget(SkillHubImportConfig config, URL target)
            throws UnknownHostException {
        String protocol = target.getProtocol().toLowerCase(Locale.ENGLISH);
        if (!HTTPS.equals(protocol) && !config.isAllowHttp()) {
            throw new IllegalArgumentException(
                    "SkillHub importer requires HTTPS endpoints unless allow-http is enabled.");
        }
        if (!config.isAllowPrivateNetwork()) {
            InetAddress[] addresses = InetAddress.getAllByName(target.getHost());
            for (InetAddress address : addresses) {
                if (isPrivateAddress(address)) {
                    throw new IllegalArgumentException(
                            "SkillHub importer rejects private network endpoints by default.");
                }
            }
        }
    }
    
    private boolean isPrivateAddress(InetAddress address) {
        return address.isAnyLocalAddress() || address.isLoopbackAddress() || address.isLinkLocalAddress()
                || address.isSiteLocalAddress() || address.isMulticastAddress();
    }
    
    private byte[] readBody(InputStream input) throws IOException {
        if (input == null) {
            return new byte[0];
        }
        try (InputStream stream = input; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int len;
            while ((len = stream.read(buffer)) >= 0) {
                output.write(buffer, 0, len);
            }
            return output.toByteArray();
        }
    }
}
