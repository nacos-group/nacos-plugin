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

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.common.utils.NamespaceUtil;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/***
 * @author onewe
 */
public class ConfigInfoMapperByOracle extends AbstractOracleMapper
		implements ConfigInfoMapper {

	private String getLimitPageSqlWithOffset(String sql, int startOffset, int pageSize) {
		return getDatabaseDialect().getLimitPageSqlWithOffset(sql, startOffset, pageSize);
	}

	private String getLimitPageSqlWithMark(String sql) {
		return getDatabaseDialect().getLimitPageSqlWithMark(sql);
	}

	@Override
	public MapperResult findConfigInfoByAppCountRows(MapperContext context) {
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);

		List<Object> sqlArgs = new ArrayList<>();
		StringBuilder sqlBuilder = new StringBuilder(
				"SELECT count(*) FROM config_info WHERE ");
		if (StringUtils.isBlank(tenantId)) {
			sqlBuilder.append(" tenant_id = '")
					.append(NamespaceUtil.getNamespaceDefaultId()).append(" ");
		}
		else {
			sqlBuilder.append(" tenant_id LIKE ? ");
			sqlArgs.add(tenantId);
		}

		sqlBuilder.append(" AND app_name = ? ");
		sqlArgs.add(appName);

		String sql = sqlBuilder.toString();
		return new MapperResult(sql, sqlArgs);
	}

	@Override
	public MapperResult configInfoLikeTenantCount(MapperContext context) {
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);

		List<Object> sqlArgs = new ArrayList<>();
		StringBuilder sqlBuilder = new StringBuilder(
				"SELECT count(*) FROM config_info WHERE ");
		if (StringUtils.isBlank(tenantId)) {
			sqlBuilder.append(" tenant_id = '")
					.append(NamespaceUtil.getNamespaceDefaultId()).append("' ");
		}
		else {
			sqlBuilder.append(" tenant_id LIKE ? ");
			sqlArgs.add(tenantId);
		}

		String sql = sqlBuilder.toString();
		return new MapperResult(sql, sqlArgs);
	}

	@Override
	public MapperResult findAllConfigInfo4Export(MapperContext context) {
		List<Long> ids = (List<Long>) context.getWhereParameter(FieldConstant.IDS);

		String sql = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,md5,gmt_create,gmt_modified,"
				+ "src_user,src_ip,c_desc,c_use,effect,c_schema,encrypted_data_key FROM config_info";
		StringBuilder where = new StringBuilder(" WHERE ");

		List<Object> paramList = new ArrayList<>();
		if (!CollectionUtils.isEmpty(ids)) {
			where.append(" id IN (");
			for (int i = 0; i < ids.size(); i++) {
				if (i != 0) {
					where.append(", ");
				}
				where.append('?');
				paramList.add(ids.get(i));
			}
			where.append(") ");
		}
		else {

			String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
			String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
			String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
			String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);

			where.append(" tenant_id = NVL(?, '")
					.append(NamespaceUtil.getNamespaceDefaultId()).append("') ");
			paramList.add(tenantId);

			if (StringUtils.isNotBlank(dataId)) {
				where.append(" AND data_id LIKE ? ");
				paramList.add(dataId);
			}
			if (StringUtils.isNotBlank(group)) {
				where.append(" AND group_id= ? ");
				paramList.add(group);
			}
			if (StringUtils.isNotBlank(appName)) {
				where.append(" AND app_name= ? ");
				paramList.add(appName);
			}
		}
		return new MapperResult(sql + where, paramList);
	}

	@Override
	public MapperResult findConfigInfoBaseLikeCountRows(MapperContext context) {
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);

		final List<Object> paramList = new ArrayList<>();
		final String sqlCountRows = "SELECT count(*) FROM config_info WHERE ";
		String where = " tenant_id='" + NamespaceUtil.getNamespaceDefaultId() + "' ";

		if (!StringUtils.isBlank(dataId)) {
			where += " AND data_id LIKE ? ";
			paramList.add(dataId);
		}
		if (!StringUtils.isBlank(group)) {
			where += " AND group_id LIKE ? ";
			paramList.add(group);
		}
		if (!StringUtils.isBlank(content)) {
			where += " AND content LIKE ? ";
			paramList.add(content);
		}
		return new MapperResult(sqlCountRows + where, paramList);
	}

	@Override
	public MapperResult findConfigInfo4PageCountRows(MapperContext context) {
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
		final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
		final String tenantId = (String) context
				.getWhereParameter(FieldConstant.TENANT_ID);
		final List<Object> paramList = new ArrayList<>();

		final String sqlCount = "SELECT count(*) FROM config_info";
		StringBuilder where = new StringBuilder(" WHERE ");

		where.append(" tenant_id=NVL(?, '").append(NamespaceUtil.getNamespaceDefaultId())
				.append("') ");
		paramList.add(tenantId);
		if (StringUtils.isNotBlank(dataId)) {
			where.append(" AND data_id=? ");
			paramList.add(dataId);
		}
		if (StringUtils.isNotBlank(group)) {
			where.append(" AND group_id=? ");
			paramList.add(group);
		}
		if (StringUtils.isNotBlank(appName)) {
			where.append(" AND app_name=? ");
			paramList.add(appName);
		}
		if (!StringUtils.isBlank(content)) {
			where.append(" AND content LIKE ? ");
			paramList.add(content);
		}
		return new MapperResult(sqlCount + where, paramList);
	}

	@Override
	public MapperResult findConfigInfoLike4PageCountRows(MapperContext context) {
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
		final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
		final String tenantId = (String) context
				.getWhereParameter(FieldConstant.TENANT_ID);

		final List<Object> paramList = new ArrayList<>();

		final String sqlCountRows = "SELECT count(*) FROM config_info";
		StringBuilder where = new StringBuilder(" WHERE ");

		if (StringUtils.isBlank(tenantId)) {
			where.append(" tenant_id='").append(NamespaceUtil.getNamespaceDefaultId())
					.append("' ");
		}
		else {
			where.append(" tenant_id LIKE ? ");
			paramList.add(tenantId);
		}

		if (!StringUtils.isBlank(dataId)) {
			where.append(" AND data_id LIKE ? ");
			paramList.add(dataId);
		}
		if (!StringUtils.isBlank(group)) {
			where.append(" AND group_id LIKE ? ");
			paramList.add(group);
		}
		if (!StringUtils.isBlank(appName)) {
			where.append(" AND app_name = ? ");
			paramList.add(appName);
		}
		if (!StringUtils.isBlank(content)) {
			where.append(" AND content LIKE ? ");
			paramList.add(content);
		}
		return new MapperResult(sqlCountRows + where, paramList);
	}

	@Override
	public MapperResult updateConfigInfoAtomicCas(MapperContext context) {
		List<Object> paramList = new ArrayList<>();

		paramList.add(context.getUpdateParameter(FieldConstant.CONTENT));
		paramList.add(context.getUpdateParameter(FieldConstant.MD5));
		paramList.add(context.getUpdateParameter(FieldConstant.SRC_IP));
		paramList.add(context.getUpdateParameter(FieldConstant.SRC_USER));
		paramList.add(context.getUpdateParameter(FieldConstant.GMT_MODIFIED));
		paramList.add(context.getUpdateParameter(FieldConstant.APP_NAME));
		paramList.add(context.getUpdateParameter(FieldConstant.C_DESC));
		paramList.add(context.getUpdateParameter(FieldConstant.C_USE));
		paramList.add(context.getUpdateParameter(FieldConstant.EFFECT));
		paramList.add(context.getUpdateParameter(FieldConstant.TYPE));
		paramList.add(context.getUpdateParameter(FieldConstant.C_SCHEMA));
		paramList.add(context.getWhereParameter(FieldConstant.TENANT_ID));
		paramList.add(context.getWhereParameter(FieldConstant.DATA_ID));
		paramList.add(context.getWhereParameter(FieldConstant.GROUP_ID));
		paramList.add(context.getWhereParameter(FieldConstant.MD5));

		String sqlBuilder = "UPDATE config_info SET "
				+ "content=?, md5 = ?, src_ip=?,src_user=?,gmt_modified=?, app_name=?,c_desc=?,c_use=?,effect=?,type=?,c_schema=? "
				+ "WHERE data_id=? AND group_id=? " + " AND tenant_id=NVL(?, '"
				+ NamespaceUtil.getNamespaceDefaultId() + "') "
				+ " AND (md5=? OR md5 IS NULL OR md5='')";
		return new MapperResult(sqlBuilder, paramList);
	}

	@Override
	public MapperResult findConfigInfoByAppFetchRows(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
		final String tenantId = (String) context
				.getWhereParameter(FieldConstant.TENANT_ID);

		List<Object> sqlArgs = new ArrayList<>();
		StringBuilder sqlBuilder = new StringBuilder(
				"SELECT id,data_id,group_id,tenant_id,app_name,content FROM config_info where ");
		if (StringUtils.isBlank(tenantId)) {
			sqlBuilder.append(" tenant_id='")
					.append(NamespaceUtil.getNamespaceDefaultId()).append("' ");
		}
		else {
			sqlBuilder.append(" tenant_id LIKE ? ");
			sqlArgs.add(tenantId);
		}

		sqlBuilder.append(" AND app_name= ?");
		sqlArgs.add(appName);

		String sql = getLimitPageSqlWithOffset(sqlBuilder.toString(), startRow, pageSize);
		return new MapperResult(sql, sqlArgs);
	}

	@Override
	public MapperResult getTenantIdList(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sql = getLimitPageSqlWithOffset(
				"SELECT tenant_id FROM config_info WHERE tenant_id != '"
						+ NamespaceUtil.getNamespaceDefaultId() + "' GROUP BY tenant_id ",
				startRow, pageSize);
		return new MapperResult(sql, Collections.emptyList());
	}

	@Override
	public MapperResult getGroupIdList(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sql = getLimitPageSqlWithOffset(
				"SELECT group_id FROM config_info WHERE tenant_id != '"
						+ NamespaceUtil.getNamespaceDefaultId() + "' GROUP BY group_id ",
				+startRow, pageSize);
		return new MapperResult(sql, Collections.emptyList());
	}

	@Override
	public MapperResult findAllConfigKey(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();

		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);

		List<Object> sqlArgs = new ArrayList<>();
		StringBuilder innerSqlBuilder = new StringBuilder(
				" SELECT id FROM config_info WHERE ");
		if (StringUtils.isBlank(tenantId)) {
			innerSqlBuilder.append(" tenant_id='")
					.append(NamespaceUtil.getNamespaceDefaultId()).append("' ");
		}
		else {
			innerSqlBuilder.append(" tenant_id LIKE ? ");
			sqlArgs.add(tenantId);
		}
		innerSqlBuilder.append(" ORDER BY id ");

		String innerSql = getLimitPageSqlWithOffset(innerSqlBuilder.toString(), startRow,
				pageSize);
		String sql = " SELECT data_id,group_id,app_name  FROM ( " + innerSql
				+ " g, config_info t WHERE g.id = t.id  ";
		return new MapperResult(sql, sqlArgs);
	}

	@Override
	public MapperResult findAllConfigInfoBaseFetchRows(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String innerSql = getLimitPageSqlWithMark(
				" SELECT id FROM config_info ORDER BY id ");
		String sql = " SELECT t.id,data_id,group_id,content,md5" + " FROM ( " + innerSql
				+ "  ) " + " g, config_info t  WHERE g.id = t.id ";
		return new MapperResult(sql, CollectionUtils.list(startRow, pageSize));
	}

	@Override
	public MapperResult findAllConfigInfoFragment(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sql = getLimitPageSqlWithOffset(
				"SELECT id,data_id,group_id,tenant_id,app_name,content,md5,gmt_modified,type,encrypted_data_key "
						+ "FROM config_info WHERE id > ? ORDER BY id ASC ",
				startRow, pageSize);
		return new MapperResult(sql,
				CollectionUtils.list(context.getWhereParameter(FieldConstant.ID)));
	}

	@Override
	public MapperResult findChangeConfigFetchRows(MapperContext context) {
		final String tenant = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
		final String tenantTmp = StringUtils.isBlank(tenant) ? StringUtils.EMPTY : tenant;
		final Timestamp startTime = (Timestamp) context
				.getWhereParameter(FieldConstant.START_TIME);
		final Timestamp endTime = (Timestamp) context
				.getWhereParameter(FieldConstant.END_TIME);
		final long lastMaxId = (long) context
				.getWhereParameter(FieldConstant.LAST_MAX_ID);
		final int pageSize = context.getPageSize();
		List<Object> paramList = new ArrayList<>();

		final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,md5,gmt_modified FROM config_info WHERE ";
		String where = " 1=1 ";
		if (!StringUtils.isBlank(dataId)) {
			where += " AND data_id LIKE ? ";
			paramList.add(dataId);
		}
		if (!StringUtils.isBlank(group)) {
			where += " AND group_id LIKE ? ";
			paramList.add(group);
		}
		if (!StringUtils.isBlank(tenantTmp)) {
			where += " AND tenant_id = ? ";
			paramList.add(tenantTmp);
		}
		if (!StringUtils.isBlank(appName)) {
			where += " AND app_name = ? ";
			paramList.add(appName);
		}
		if (startTime != null) {
			where += " AND gmt_modified >=? ";
			paramList.add(startTime);
		}
		if (endTime != null) {
			where += " AND gmt_modified <=? ";
			paramList.add(endTime);
		}
		String originSql = sqlFetchRows + where + " AND id > " + lastMaxId
				+ " ORDER BY id ASC";
		String sql = getLimitPageSqlWithOffset(originSql, 0, pageSize);
		return new MapperResult(sql, paramList);
	}

	@Override
	public MapperResult listGroupKeyMd5ByPageFetchRows(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String innerSql = getLimitPageSqlWithOffset(
				" SELECT id FROM config_info ORDER BY id ", startRow, pageSize);
		String sql = " SELECT t.id,data_id,group_id,tenant_id,app_name,md5,type,gmt_modified,encrypted_data_key FROM "
				+ "( " + innerSql + " ) g, config_info t WHERE g.id = t.id";
		return new MapperResult(sql, Collections.emptyList());
	}

	@Override
	public MapperResult findConfigInfoBaseLikeFetchRows(MapperContext context) {
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
		final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,content FROM config_info WHERE ";
		String where = " tenant_id='" + NamespaceUtil.getNamespaceDefaultId() + "' ";
		List<Object> paramList = new ArrayList<>();
		if (!StringUtils.isBlank(dataId)) {
			where += " AND data_id LIKE ? ";
			paramList.add(dataId);
		}
		if (!StringUtils.isBlank(group)) {
			where += " AND group_id LIKE ";
			paramList.add(group);
		}
		if (!StringUtils.isBlank(content)) {
			where += " AND content LIKE ? ";
			paramList.add(content);
		}
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sql = getLimitPageSqlWithOffset(sqlFetchRows + where, startRow, pageSize);
		return new MapperResult(sql, paramList);
	}

	@Override
	public MapperResult findConfigInfo4PageFetchRows(MapperContext context) {
		final String tenant = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
		final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
		List<Object> paramList = new ArrayList<>();
		final String sql = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,encrypted_data_key FROM config_info";
		StringBuilder where = new StringBuilder(" WHERE ");

		where.append(" tenant_id=NVL(?, '").append(NamespaceUtil.getNamespaceDefaultId())
				.append("') ");
		paramList.add(tenant);

		if (StringUtils.isNotBlank(dataId)) {
			where.append(" AND data_id=? ");
			paramList.add(dataId);
		}
		if (StringUtils.isNotBlank(group)) {
			where.append(" AND group_id=? ");
			paramList.add(group);
		}
		if (StringUtils.isNotBlank(appName)) {
			where.append(" AND app_name=? ");
			paramList.add(appName);
		}
		if (!StringUtils.isBlank(content)) {
			where.append(" AND content LIKE ? ");
			paramList.add(content);
		}
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String resultSql = getLimitPageSqlWithOffset(sql + where, startRow, pageSize);
		return new MapperResult(resultSql, paramList);
	}

	@Override
	public MapperResult findConfigInfoBaseByGroupFetchRows(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();

		String groupId = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);

		List<Object> sqlArgs = new ArrayList<>();
		sqlArgs.add(groupId);
		sqlArgs.add(tenantId);

		String sql = "SELECT id,data_id,group_id,content FROM config_info WHERE group_id=? and "
				+ " tenant_id=NVL(?, '" + NamespaceUtil.getNamespaceDefaultId() + "') ";
		String resultSql = getLimitPageSqlWithOffset(sql, startRow, pageSize);
		return new MapperResult(resultSql, sqlArgs);
	}

	@Override
	public MapperResult findConfigInfoLike4PageFetchRows(MapperContext context) {
		final String tenant = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
		final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
		final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,app_name,content,encrypted_data_key FROM config_info";
		StringBuilder where = new StringBuilder(" WHERE ");
		List<Object> paramList = new ArrayList<>();

		if (StringUtils.isBlank(tenant)) {
			where.append(" tenant_id='").append(NamespaceUtil.getNamespaceDefaultId())
					.append("' ");
		}
		else {
			where.append(" tenant_id LIKE ? ");
			paramList.add(tenant);
		}

		if (!StringUtils.isBlank(dataId)) {
			where.append(" AND data_id LIKE ? ");
			paramList.add(dataId);
		}
		if (!StringUtils.isBlank(group)) {
			where.append(" AND group_id LIKE ? ");
			paramList.add(group);
		}
		if (!StringUtils.isBlank(appName)) {
			where.append(" AND app_name = ? ");
			paramList.add(appName);
		}
		if (!StringUtils.isBlank(content)) {
			where.append(" AND content LIKE ? ");
			paramList.add(content);
		}
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String sql = getLimitPageSqlWithOffset(sqlFetchRows + where, startRow, pageSize);
		return new MapperResult(sql, paramList);
	}

	@Override
	public MapperResult findAllConfigInfoFetchRows(MapperContext context) {
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);

		List<Object> sqlArgs = new ArrayList<>();
		StringBuilder sqlBuilder = new StringBuilder("SELECT id FROM config_info WHERE ");
		if (StringUtils.isBlank(tenantId)) {
			sqlBuilder.append(" tenant_id='")
					.append(NamespaceUtil.getNamespaceDefaultId()).append("' ");
		}
		else {
			sqlBuilder.append(" tenant_id LIKE ? ");
			sqlArgs.add(tenantId);
		}

		sqlBuilder.append(" ORDER BY id ");

		sqlArgs.add(context.getStartRow());
		sqlArgs.add(context.getPageSize());

		String innerSql = getLimitPageSqlWithMark(sqlBuilder.toString());
		String sql = " SELECT t.id,data_id,group_id,tenant_id,app_name,content,md5 "
				+ " FROM ( " + innerSql + " )" + " g, config_info t  WHERE g.id = t.id ";
		return new MapperResult(sql, sqlArgs);
	}

}
