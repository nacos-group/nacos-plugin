/*
 * Copyright 1999-2023 Alibaba Group Holding Ltd.
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
package com.alibaba.nacos.plugin.datasource.impl.oracle;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import com.alibaba.nacos.common.utils.NamespaceUtil;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoBetaMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/***
 * @author onewe
 */
public class ConfigInfoBetaMapperByOracle extends AbstractOracleMapper
		implements ConfigInfoBetaMapper {

	private String getLimitPageSqlWithOffset(String sql, int startRow, int pageSize) {
		return getDatabaseDialect().getLimitPageSqlWithOffset(sql, startRow, pageSize);
	}

	@Override
	public MapperResult findAllConfigInfoBetaForDumpAllFetchRows(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sqlInner = getLimitPageSqlWithOffset(
				"SELECT id FROM config_info_beta  ORDER BY id ", startRow, pageSize);
		String sql = " SELECT t.id,data_id,group_id,tenant_id,app_name,content,md5,gmt_modified,beta_ips,encrypted_data_key "
				+ " FROM ( " + sqlInner + "  )"
				+ "  g, config_info_beta t WHERE g.id = t.id ";
		return new MapperResult(sql, Collections.emptyList());
	}
	
	@Override
	public MapperResult updateConfigInfo4BetaCas(MapperContext context) {
		final String sql = "UPDATE config_info_beta SET content = ?,md5 = ?,beta_ips = ?,src_ip = ?,src_user = ?,gmt_modified = ?,app_name = ? "
				+ "WHERE data_id = ? AND group_id = ? AND tenant_id = NVL(?, '"+ NamespaceUtil.getNamespaceDefaultId() +"') AND (md5 = ? OR md5 is null OR md5 = '')";
		
		List<Object> paramList = new ArrayList<>();
		
		paramList.add(context.getUpdateParameter(FieldConstant.CONTENT));
		paramList.add(context.getUpdateParameter(FieldConstant.MD5));
		paramList.add(context.getUpdateParameter(FieldConstant.BETA_IPS));
		paramList.add(context.getUpdateParameter(FieldConstant.SRC_IP));
		paramList.add(context.getUpdateParameter(FieldConstant.SRC_USER));
		paramList.add(context.getUpdateParameter(FieldConstant.GMT_MODIFIED));
		paramList.add(context.getUpdateParameter(FieldConstant.APP_NAME));
		
		paramList.add(context.getWhereParameter(FieldConstant.DATA_ID));
		paramList.add(context.getWhereParameter(FieldConstant.GROUP_ID));
		paramList.add(context.getWhereParameter(FieldConstant.TENANT_ID));
		paramList.add(context.getWhereParameter(FieldConstant.MD5));
		
		return new MapperResult(sql, paramList);
	}
}
