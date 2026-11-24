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

/**
 * HTTP response for SkillHub API calls.
 *
 * @author nacos
 */
public class SkillHubHttpResponse {
    
    private final String url;
    
    private final int statusCode;
    
    private final byte[] body;
    
    private final String location;
    
    public SkillHubHttpResponse(String url, int statusCode, byte[] body) {
        this(url, statusCode, body, null);
    }
    
    public SkillHubHttpResponse(String url, int statusCode, byte[] body, String location) {
        this.url = url;
        this.statusCode = statusCode;
        this.body = body == null ? new byte[0] : body;
        this.location = location;
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
    
    public String getLocation() {
        return location;
    }
    
    public boolean isSuccess() {
        return statusCode >= 200 && statusCode < 300;
    }
    
    public boolean isRedirect() {
        return statusCode >= 300 && statusCode < 400;
    }
}
