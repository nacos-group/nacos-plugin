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
import com.alibaba.nacos.plugin.ai.importer.skillssh.SkillsShImportConfig;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.Locale;

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
    
    @Override
    public SkillsShHttpResponse get(SkillsShImportConfig config, String url) throws Exception {
        URL target = new URL(url);
        validateTarget(config, target);
        HttpURLConnection connection = (HttpURLConnection) target.openConnection();
        connection.setRequestMethod("GET");
        connection.setConnectTimeout(config.getConnectTimeoutMillis());
        connection.setReadTimeout(config.getReadTimeoutMillis());
        connection.setRequestProperty("Accept", "application/json");
        String token = config.getToken();
        if (StringUtils.isNotBlank(token)) {
            // Authenticated skills.sh v1 APIs accept Bearer tokens from ConfigSpec.
            connection.setRequestProperty("Authorization", "Bearer " + token.trim());
        }
        int statusCode = connection.getResponseCode();
        InputStream stream = statusCode >= 400 ? connection.getErrorStream() : connection.getInputStream();
        byte[] body = readBody(stream);
        connection.disconnect();
        return new SkillsShHttpResponse(url, statusCode, body);
    }
    
    private void validateTarget(SkillsShImportConfig config, URL target)
            throws UnknownHostException {
        String protocol = target.getProtocol().toLowerCase(Locale.ENGLISH);
        if (!HTTPS.equals(protocol) && !config.isAllowHttp()) {
            throw new IllegalArgumentException("skills.sh importer requires HTTPS endpoints unless allow-http is enabled.");
        }
        /*
         * Private network access is opt-in to avoid accidentally turning importer
         * configuration into a server-side request path to local infrastructure.
         */
        if (!config.isAllowPrivateNetwork()) {
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
