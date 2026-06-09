/*
 * Copyright 1999-2026 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 */
package com.alibaba.nacos.plugin.ai.importer.skillssh;

import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportService;
import com.alibaba.nacos.plugin.ai.importer.spi.AiResourceImportServiceBuilder;

import java.util.Properties;

/**
 * Builder for the skills.sh AI resource import service.
 *
 * @author elnafateh
 */
public class SkillsShImportServiceBuilder implements AiResourceImportServiceBuilder {
    
    public static final String IMPORTER_TYPE = "skills-sh";
    
    @Override
    public String importerType() {
        return IMPORTER_TYPE;
    }
    
    @Override
    public AiResourceImportService build(Properties properties) {
        return new SkillsShImportService();
    }
}
