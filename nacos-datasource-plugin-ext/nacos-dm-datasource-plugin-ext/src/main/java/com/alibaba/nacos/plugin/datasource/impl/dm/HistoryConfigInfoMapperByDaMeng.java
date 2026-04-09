/*
 * Copyright 1999-2022 Alibaba Group Holding Ltd.
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

package com.alibaba.nacos.plugin.datasource.impl.dm;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.constants.PrimaryKeyConstant;
import com.alibaba.nacos.plugin.datasource.mapper.HistoryConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/**
 * The dameng implementation of HistoryConfigInfoMapper.
 *
 * @author Xiao Yong
 **/
public class HistoryConfigInfoMapperByDaMeng extends AbstractMapperByDaMeng implements HistoryConfigInfoMapper {
    
    @Override
    public MapperResult removeConfigHistory(MapperContext context) {
        String sql = getLimitTopSqlWithMark("DELETE FROM his_config_info WHERE gmt_modified < ? ");
        return new MapperResult(sql, CollectionUtils.list(context.getWhereParameter(FieldConstant.GMT_MODIFIED),
                        context.getWhereParameter(FieldConstant.LIMIT_SIZE)));
    }
    
    @Override
    public MapperResult pageFindConfigHistoryFetchRows(MapperContext context) {
        String sql = getLimitPageSqlWithOffset(
                "SELECT nid,data_id,group_id,tenant_id,app_name,src_ip,src_user,op_type,gmt_create,gmt_modified "
                        + " FROM his_config_info "
                        + " WHERE data_id = ? AND group_id = ? AND tenant_id = ? ORDER BY nid DESC ",
                context.getStartRow(), context.getPageSize());
        
        return new MapperResult(sql, CollectionUtils.list(context.getWhereParameter(FieldConstant.DATA_ID),
                context.getWhereParameter(FieldConstant.GROUP_ID), context.getWhereParameter(FieldConstant.TENANT_ID)));
    }
    
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.DM;
    }

    @Override
    public String[] getPrimaryKeyGeneratedKeys() {
        return PrimaryKeyConstant.UPPER_RETURN_PRIMARY_KEYS;
    }
    
    private String getLimitPageSqlWithOffset(String sql, int offset, int limit) {
        return getDialect().getLimitPageSqlWithOffset(sql,offset,limit);
    }
    
    private String getLimitTopSqlWithMark(String sql) {
        return getDialect().getLimitTopSqlWithMark(sql);
    }
}
