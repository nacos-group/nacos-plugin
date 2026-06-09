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

/**
 * HTTP response for skills.sh API calls.
 *
 * @author elnafateh
 */
public class SkillsShHttpResponse {
    
    private final String url;
    
    private final int statusCode;
    
    private final byte[] body;
    
    public SkillsShHttpResponse(String url, int statusCode, byte[] body) {
        this.url = url;
        this.statusCode = statusCode;
        this.body = body == null ? new byte[0] : body;
    }
    
    public String getUrl() {
        return url;
    }
    
    public int getStatusCode() {
        return statusCode;
    }
    
    public byte[] getBody() {
        return body;
    }
    
    public boolean isSuccess() {
        return statusCode >= 200 && statusCode < 300;
    }
}
