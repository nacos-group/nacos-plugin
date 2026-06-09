/*
 * Copyright 1999-2026 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 */
package com.alibaba.nacos.plugin.ai.importer.skillssh.http;

import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.Locale;
import java.util.Map;

/**
 * Default URLConnection-based skills.sh HTTP client.
 *
 * @author elnafateh
 */
public class DefaultSkillsShHttpClient implements SkillsShHttpClient {
    
    public static final String PROPERTY_TOKEN = "token";
    
    public static final String PROPERTY_AUTH_TOKEN = "auth-token";
    
    public static final String PROPERTY_AUTH_TOKEN_CAMEL = "authToken";
    
    public static final String PROPERTY_ALLOW_HTTP = "allow-http";
    
    public static final String PROPERTY_ALLOW_HTTP_CAMEL = "allowHttp";
    
    public static final String PROPERTY_ALLOW_PRIVATE_NETWORK = "allow-private-network";
    
    public static final String PROPERTY_ALLOW_PRIVATE_NETWORK_CAMEL = "allowPrivateNetwork";
    
    private static final String HTTPS = "https";
    
    private static final int DEFAULT_CONNECT_TIMEOUT_MILLIS = 3000;
    
    private static final int DEFAULT_READ_TIMEOUT_MILLIS = 10000;
    
    @Override
    public SkillsShHttpResponse get(AiResourceImportSource source, String url) throws Exception {
        URL target = new URL(url);
        validateTarget(source, target);
        HttpURLConnection connection = (HttpURLConnection) target.openConnection();
        connection.setRequestMethod("GET");
        connection.setConnectTimeout(resolveConnectTimeout(source));
        connection.setReadTimeout(resolveReadTimeout(source));
        connection.setRequestProperty("Accept", "application/json");
        String token = getProperty(source, PROPERTY_TOKEN, PROPERTY_AUTH_TOKEN, PROPERTY_AUTH_TOKEN_CAMEL);
        if (StringUtils.isNotBlank(token)) {
            connection.setRequestProperty("Authorization", "Bearer " + token.trim());
        }
        int statusCode = connection.getResponseCode();
        InputStream stream = statusCode >= 400 ? connection.getErrorStream() : connection.getInputStream();
        byte[] body = readBody(stream);
        connection.disconnect();
        return new SkillsShHttpResponse(url, statusCode, body);
    }
    
    private void validateTarget(AiResourceImportSource source, URL target) throws UnknownHostException {
        String protocol = target.getProtocol().toLowerCase(Locale.ENGLISH);
        if (!HTTPS.equals(protocol) && !getBoolean(source, PROPERTY_ALLOW_HTTP, PROPERTY_ALLOW_HTTP_CAMEL)) {
            throw new IllegalArgumentException("skills.sh importer requires HTTPS endpoints unless allow-http is enabled.");
        }
        if (!getBoolean(source, PROPERTY_ALLOW_PRIVATE_NETWORK, PROPERTY_ALLOW_PRIVATE_NETWORK_CAMEL)) {
            InetAddress[] addresses = InetAddress.getAllByName(target.getHost());
            for (InetAddress address : addresses) {
                if (isPrivateAddress(address)) {
                    throw new IllegalArgumentException("skills.sh importer rejects private network endpoints by default.");
                }
            }
        }
    }
    
    private boolean isPrivateAddress(InetAddress address) {
        return address.isAnyLocalAddress() || address.isLoopbackAddress() || address.isLinkLocalAddress()
                || address.isSiteLocalAddress() || address.isMulticastAddress();
    }
    
    private int resolveConnectTimeout(AiResourceImportSource source) {
        return source.getConnectTimeoutMillis() > 0 ? source.getConnectTimeoutMillis() : DEFAULT_CONNECT_TIMEOUT_MILLIS;
    }
    
    private int resolveReadTimeout(AiResourceImportSource source) {
        return source.getReadTimeoutMillis() > 0 ? source.getReadTimeoutMillis() : DEFAULT_READ_TIMEOUT_MILLIS;
    }
    
    private boolean getBoolean(AiResourceImportSource source, String kebabKey, String camelKey) {
        String value = getProperty(source, kebabKey, camelKey);
        return StringUtils.isNotBlank(value) && Boolean.parseBoolean(value);
    }
    
    private String getProperty(AiResourceImportSource source, String... keys) {
        Map<String, String> properties = source == null ? null : source.getProperties();
        if (properties == null) {
            return null;
        }
        for (String key : keys) {
            String value = properties.get(key);
            if (StringUtils.isNotBlank(value)) {
                return value;
            }
        }
        return null;
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
