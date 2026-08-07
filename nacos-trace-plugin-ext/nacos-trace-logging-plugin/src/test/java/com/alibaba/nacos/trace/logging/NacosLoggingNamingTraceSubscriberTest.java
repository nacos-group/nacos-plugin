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

package com.alibaba.nacos.trace.logging;

import com.alibaba.nacos.api.plugin.PluginStateCheckerHolder;
import com.alibaba.nacos.api.plugin.PluginType;
import com.alibaba.nacos.common.trace.DeregisterInstanceReason;
import com.alibaba.nacos.common.trace.event.TraceEvent;
import com.alibaba.nacos.common.trace.event.naming.DeregisterInstanceTraceEvent;
import com.alibaba.nacos.common.trace.event.naming.RegisterInstanceTraceEvent;
import com.alibaba.nacos.common.spi.PluginRegistryUtils;
import com.alibaba.nacos.plugin.trace.NacosTracePluginManager;
import com.alibaba.nacos.plugin.trace.spi.NacosTraceSubscriber;
import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * {@link NacosLoggingNamingTraceSubscriber} unit test.
 *
 * @author Nacos
 */
public class NacosLoggingNamingTraceSubscriberTest {

    private static final Logger LOGGER = LoggerFactory.getLogger(
            NacosLoggingNamingTraceSubscriberTest.class);

    private static final String PLUGIN_NAME = "namingLogging";

    private NacosLoggingNamingTraceSubscriber subscriber;

    @Before
    public void setUp() {
        subscriber = new NacosLoggingNamingTraceSubscriber();
    }

    @After
    public void tearDown() {
        PluginStateCheckerHolder.setInstance(null);
    }

    @Test
    public void testUnifiedDiscovery() {
        Map<String, NacosTraceSubscriber> plugins = NacosTracePluginManager.getInstance()
                .getAllPlugins();

        Assert.assertTrue(plugins.containsKey(PLUGIN_NAME));
        Assert.assertTrue(plugins.get(PLUGIN_NAME) instanceof NacosLoggingNamingTraceSubscriber);
    }

    @Test
    public void testFirstWinsIdentity() {
        Map<String, NacosTraceSubscriber> plugins = new HashMap<>();
        NacosTraceSubscriber first = new NacosLoggingNamingTraceSubscriber();
        NacosTraceSubscriber duplicate = new NacosLoggingNamingTraceSubscriber();

        Assert.assertTrue(PluginRegistryUtils.registerFirst(plugins, PluginType.TRACE.getType(),
                first.getName(), first, LOGGER));
        Assert.assertFalse(PluginRegistryUtils.registerFirst(plugins, PluginType.TRACE.getType(),
                duplicate.getName(), duplicate, LOGGER));

        Assert.assertSame(first, plugins.get(PLUGIN_NAME));
    }

    @Test
    public void testUnifiedPluginStateFiltering() {
        PluginStateCheckerHolder.setInstance((pluginType, pluginName) -> PluginType.TRACE
                .getType().equals(pluginType) && !PLUGIN_NAME.equals(pluginName));

        Collection<NacosTraceSubscriber> disabledSubscribers = NacosTracePluginManager
                .getInstance().getAllTraceSubscribers();

        Assert.assertFalse(disabledSubscribers.stream()
                .anyMatch(each -> PLUGIN_NAME.equals(each.getName())));

        PluginStateCheckerHolder.setInstance((pluginType, pluginName) -> PluginType.TRACE
                .getType().equals(pluginType) && PLUGIN_NAME.equals(pluginName));

        Collection<NacosTraceSubscriber> enabledSubscribers = NacosTracePluginManager
                .getInstance().getAllTraceSubscribers();

        Assert.assertTrue(enabledSubscribers.stream()
                .anyMatch(each -> PLUGIN_NAME.equals(each.getName())));
    }

    @Test
    public void testZeroConfigContract() {
        Assert.assertFalse(subscriber.isConfigurable());
        Assert.assertTrue(subscriber.getConfigDefinitions().isEmpty());
        Assert.assertTrue(subscriber.getCurrentConfig().isEmpty());

        subscriber.applyConfig(Collections.singletonMap("ignored", "value"));

        Assert.assertTrue(subscriber.getCurrentConfig().isEmpty());
    }

    @Test
    public void testSubscribeTypes() {
        List<Class<? extends TraceEvent>> subscribeTypes = subscriber.subscribeTypes();

        Assert.assertEquals(2, subscribeTypes.size());
        Assert.assertTrue(subscribeTypes.contains(RegisterInstanceTraceEvent.class));
        Assert.assertTrue(subscribeTypes.contains(DeregisterInstanceTraceEvent.class));
    }

    @Test
    public void testEventDelivery() {
        subscriber.onEvent(new RegisterInstanceTraceEvent(1L, "127.0.0.1", true, "public",
                "DEFAULT_GROUP", "nacos.test", "127.0.0.1", 8848));
        subscriber.onEvent(new DeregisterInstanceTraceEvent(2L, "127.0.0.1", false,
                DeregisterInstanceReason.REQUEST, "public", "DEFAULT_GROUP", "nacos.test",
                "127.0.0.1", 8848));
    }

    @Test
    public void testIgnoresUnsubscribedEvent() {
        subscriber.onEvent(new TraceEvent("OTHER_TRACE_EVENT", 3L, "public", "DEFAULT_GROUP",
                "nacos.test"));
    }
}
