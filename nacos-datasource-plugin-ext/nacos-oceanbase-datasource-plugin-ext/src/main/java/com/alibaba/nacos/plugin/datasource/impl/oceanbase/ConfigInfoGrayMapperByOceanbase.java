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

package com.alibaba.nacos.plugin.datasource.impl.oceanbase;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoGrayMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * @author Ken
 */
public class ConfigInfoGrayMapperByOceanbase extends AbstractOceanbaseMapper implements ConfigInfoGrayMapper {
    
    @Override
    public MapperResult updateConfigInfo4GrayCas(MapperContext context) {
        String sql = "UPDATE config_info_gray SET content = ?,md5 = ?,src_ip = ?,src_user = ?,gmt_modified = ?,app_name = ?,gray_rule=? "
                + " WHERE data_id = ? AND group_id = ? AND tenant_id = NVL(?, '"+ DEFAULT_NAMESPACE_ID +"') "
                + " AND gray_name=? AND (md5 = ? OR md5 is null OR md5 = '')";

		List<Object> paramList = new ArrayList<>();

		paramList.add(context.getUpdateParameter(FieldConstant.CONTENT));
		paramList.add(context.getUpdateParameter(FieldConstant.MD5));
		paramList.add(context.getUpdateParameter(FieldConstant.SRC_IP));
		paramList.add(context.getUpdateParameter(FieldConstant.SRC_USER));
		paramList.add(context.getUpdateParameter(FieldConstant.GMT_MODIFIED));
		paramList.add(context.getUpdateParameter(FieldConstant.APP_NAME));
        paramList.add(context.getUpdateParameter(FieldConstant.GRAY_RULE));

		paramList.add(context.getWhereParameter(FieldConstant.DATA_ID));
		paramList.add(context.getWhereParameter(FieldConstant.GROUP_ID));
		paramList.add(context.getWhereParameter(FieldConstant.TENANT_ID));
        paramList.add(context.getWhereParameter(FieldConstant.GRAY_NAME));
		paramList.add(context.getWhereParameter(FieldConstant.MD5));

		return new MapperResult(sql, paramList);
    }
    
    @Override
    public MapperResult findChangeConfig(MapperContext context) {
        String sql =getLimitTopSqlWithMark(
                "SELECT id, data_id, group_id, tenant_id, app_name,content,gray_name,gray_rule,md5, gmt_modified, encrypted_data_key "
                        + "FROM config_info_gray WHERE " + "gmt_modified >= ? and id > ? order by id  ");
        return new MapperResult(sql, CollectionUtils.list(context.getWhereParameter(FieldConstant.START_TIME),
                context.getWhereParameter(FieldConstant.LAST_MAX_ID),
                context.getWhereParameter(FieldConstant.PAGE_SIZE)));
    }
    
    @Override
    public MapperResult findAllConfigInfoGrayForDumpAllFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sqlInner = getLimitPageSqlWithOffset(
				"SELECT id FROM config_info_gray  ORDER BY id ", startRow, pageSize);
		String sql = " SELECT t.id,data_id,group_id,tenant_id,gray_name,app_name,content,md5,gmt_modified "
				+ " FROM ( " + sqlInner + "  )"
				+ "  g, config_info_gray t WHERE g.id = t.id ";
		return new MapperResult(sql, Collections.emptyList());
    }
    
    private String getLimitTopSqlWithMark(String sql) {
		return getDatabaseDialect().getLimitTopSqlWithMark(sql);
	}
    
    private String getLimitPageSqlWithOffset(String sql, int startOffset, int pageSize) {
		return getDatabaseDialect().getLimitPageSqlWithOffset(sql, startOffset, pageSize);
	}
}
