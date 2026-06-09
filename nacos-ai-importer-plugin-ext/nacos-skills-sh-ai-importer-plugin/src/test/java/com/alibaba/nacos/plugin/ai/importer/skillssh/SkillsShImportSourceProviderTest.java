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

import com.alibaba.nacos.plugin.ai.importer.model.AiResourceImportSource;
import com.alibaba.nacos.plugin.ai.importer.skillssh.http.DefaultSkillsShHttpClient;
import org.junit.Test;

import java.util.Collection;
import java.util.Properties;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * Unit tests for {@link SkillsShImportSourceProvider}.
 *
 * @author elnafateh
 */
public class SkillsShImportSourceProviderTest {
    
    @Test
    public void testDisabledByDefault() throws Exception {
        Collection<AiResourceImportSource> sources = new SkillsShImportSourceProvider().loadSources(new Properties());
        assertTrue(sources.isEmpty());
    }
    
    @Test
    public void testLoadEnabledSourceWithDefaults() throws Exception {
        Properties properties = new Properties();
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.enabled", "true");
        Collection<AiResourceImportSource> sources = new SkillsShImportSourceProvider().loadSources(properties);
        AiResourceImportSource source = sources.iterator().next();
        assertEquals("skills-sh", source.getSourceId());
        assertEquals("skills-sh", source.getPluginName());
        assertEquals("https://skills.sh", source.getEndpoint());
        assertEquals(1, source.getResourceTypes().size());
        assertEquals("skill", source.getResourceTypes().get(0));
        assertTrue(source.isEnabled());
        assertNull(source.getProperties());
    }
    
    @Test
    public void testLoadConfiguredSourceProperties() throws Exception {
        Properties properties = new Properties();
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.enabled", "true");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.source-id", "skills-private");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.endpoint", "https://example.com");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.token", "token-1");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.allow-http", "true");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.allow-private-network", "true");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.max-item-count", "20");
        properties.setProperty("nacos.plugin.ai.importer.skills.skills-sh.max-artifact-size", "1024");
        AiResourceImportSource source = new SkillsShImportSourceProvider().loadSources(properties).iterator().next();
        assertEquals("skills-private", source.getSourceId());
        assertEquals("https://example.com", source.getEndpoint());
        assertEquals(20, source.getMaxItemCount());
        assertEquals(1024, source.getMaxArtifactSize());
        assertEquals("token-1", source.getProperties().get(DefaultSkillsShHttpClient.PROPERTY_TOKEN));
        assertEquals("true", source.getProperties().get(DefaultSkillsShHttpClient.PROPERTY_ALLOW_HTTP));
        assertEquals("true", source.getProperties().get(DefaultSkillsShHttpClient.PROPERTY_ALLOW_PRIVATE_NETWORK));
        assertFalse(source.getProperties().containsKey("missing"));
    }
}
