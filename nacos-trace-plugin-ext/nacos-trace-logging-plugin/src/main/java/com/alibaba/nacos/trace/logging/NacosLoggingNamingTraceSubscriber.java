package com.alibaba.nacos.trace.logging;

import com.alibaba.nacos.common.trace.event.TraceEvent;
import com.alibaba.nacos.common.trace.event.naming.DeregisterInstanceTraceEvent;
import com.alibaba.nacos.common.trace.event.naming.RegisterInstanceTraceEvent;
import com.alibaba.nacos.plugin.trace.spi.NacosTraceSubscriber;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.LinkedList;
import java.util.List;

/**
 * Nacos logging naming trace subscriber.
 *
 * @author xiweng.yy
 */
public class NacosLoggingNamingTraceSubscriber implements NacosTraceSubscriber {
    
    private static final Logger LOGGER = LoggerFactory.getLogger(NacosLoggingNamingTraceSubscriber.class);
    
    private static final String NAME = "namingLogging";
    
    @Override
    public String getName() {
        return NAME;
    }
    
    @Override
    public void onEvent(TraceEvent event) {
        if (event instanceof RegisterInstanceTraceEvent) {
            loggingRegisterInstance((RegisterInstanceTraceEvent) event);
        } else if (event instanceof DeregisterInstanceTraceEvent) {
            loggingDeregisterInstance((DeregisterInstanceTraceEvent) event);
        }
    }
    
    private void loggingRegisterInstance(RegisterInstanceTraceEvent event) {
        LOGGER.info("[DEMO] namespaceId: {}, groupName: {}, serviceName: {} register a new instance {} by {}",
                event.getNamespace(), event.getGroup(), event.getName(), event.toInetAddr(),
                event.isRpc() ? "gRPC" : "HTTP");
    }
    
    private void loggingDeregisterInstance(DeregisterInstanceTraceEvent event) {
        LOGGER.info("[DEMO] namespaceId: {}, groupName: {}, serviceName: {} deregister an instance {} for reason {}",
                event.getNamespace(), event.getGroup(), event.getName(), event.toInetAddr(),
                event.getReason());
    }
    
    @Override
    public List<Class<? extends TraceEvent>> subscribeTypes() {
        List<Class<? extends TraceEvent>> result = new LinkedList<>();
        result.add(RegisterInstanceTraceEvent.class);
        result.add(DeregisterInstanceTraceEvent.class);
        return result;
    }
}
