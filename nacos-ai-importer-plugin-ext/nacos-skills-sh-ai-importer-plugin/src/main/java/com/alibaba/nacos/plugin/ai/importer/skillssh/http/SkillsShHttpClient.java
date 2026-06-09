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

import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;

/**
 * HTTP client abstraction for skills.sh API calls.
 *
 * @author elnafateh
 */
public interface SkillsShHttpClient {
    
    /**
     * Execute an HTTP GET request.
     *
     * @param source import source
     * @param url target URL
     * @return response
     * @throws Exception if the request fails
     */
    SkillsShHttpResponse get(AiResourceImportSource source, String url) throws Exception;
}
