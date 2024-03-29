/*
 * Copyright 1999-2021 Alibaba Group Holding Ltd.
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

package com.alibaba.nacos.plugin.config;

import com.alibaba.nacos.common.executor.ExecutorFactory;
import com.alibaba.nacos.common.executor.NameThreadFactory;
import com.alibaba.nacos.common.utils.ClassUtils;
import com.alibaba.nacos.common.utils.ThreadUtils;

import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * @author liyunfei
 **/
public class ConfigChangePluginExecutor {

    private static final ScheduledExecutorService ASYNC_CONFIG_CHANGE_NOTIFY_PLUGIN_EXECUTOR = ExecutorFactory.Managed
            .newScheduledExecutorService(ClassUtils.getCanonicalName(ConfigChangePluginExecutor.class),
                    ThreadUtils.getSuitableThreadCount(),
                    new NameThreadFactory("com.alibaba.nacos.config.plugin.webhookService"));

    public static void executeAsyncConfigChangePluginTask(Runnable runnable) {
        ASYNC_CONFIG_CHANGE_NOTIFY_PLUGIN_EXECUTOR.execute(runnable);
    }

    public static void scheduleAsyncConfigChangePluginTask(Runnable command, long delay, TimeUnit unit) {
        ASYNC_CONFIG_CHANGE_NOTIFY_PLUGIN_EXECUTOR.schedule(command, delay,  unit);
    }

}
