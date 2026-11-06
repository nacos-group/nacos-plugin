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

import com.alibaba.nacos.plugin.ai.importer.skillhub.SkillHubImportConfig;

/**
 * HTTP client abstraction for SkillHub API calls.
 *
 * @author nacos
 */
public interface SkillHubHttpClient {
    
    /**
     * Execute an HTTP GET request.
     *
     * @param config import configuration
     * @param url target URL
     * @param followRedirects whether to follow redirects automatically
     * @param hostHeader optional Host header override (used after redirect rewrite)
     * @param withAuth whether to send the Bearer token
     * @return response
     * @throws Exception if the request fails
     */
    SkillHubHttpResponse get(SkillHubImportConfig config, String url, boolean followRedirects,
            String hostHeader, boolean withAuth) throws Exception;
}
