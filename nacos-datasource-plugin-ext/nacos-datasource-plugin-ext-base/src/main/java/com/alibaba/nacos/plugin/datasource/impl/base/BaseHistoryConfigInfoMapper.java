package com.alibaba.nacos.plugin.datasource.impl.base;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.HistoryConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;
/**
 * The base implementation of HistoryConfigInfo.
 *
 * @author floor07
 **/
public abstract class BaseHistoryConfigInfoMapper extends AbstractMapper implements HistoryConfigInfoMapper {

    @Override
    public MapperResult removeConfigHistory(MapperContext context) {
        String sql = DatabaseDialectManager.getInstance().getDialect(getDataSource()).getLimitTopSqlWithMark("DELETE FROM his_config_info WHERE gmt_modified < ? ");
        return new MapperResult(sql, CollectionUtils.list(new Object[]{context.getWhereParameter("startTime"), context.getWhereParameter("limitSize")}));
    }
    @Override
    public MapperResult pageFindConfigHistoryFetchRows(MapperContext context) {
        String sql = DatabaseDialectManager.getInstance().getDialect(getDataSource()).getLimitPageSqlWithOffset(
                "SELECT nid,data_id,group_id,tenant_id,app_name,src_ip,src_user,op_type,gmt_create,gmt_modified FROM his_config_info WHERE data_id = ? AND group_id = ? AND tenant_id = ? ORDER BY nid DESC "
                ,context.getStartRow() ,context.getPageSize());
        return new MapperResult(sql, CollectionUtils.list(new Object[]{context.getWhereParameter("dataId"), context.getWhereParameter("groupId"), context.getWhereParameter("tenantId")}));
    }
}
