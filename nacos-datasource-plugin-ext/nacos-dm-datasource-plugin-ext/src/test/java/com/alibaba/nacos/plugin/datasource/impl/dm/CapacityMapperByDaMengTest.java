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

import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.impl.mysql.GroupCapacityMapperByMysql;
import com.alibaba.nacos.plugin.datasource.impl.mysql.TenantCapacityMapperByMySql;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;
import org.junit.Test;

import java.util.Arrays;
import java.util.List;
import java.util.function.BiFunction;

import static org.junit.Assert.assertEquals;

public class CapacityMapperByDaMengTest {

    @Test
    public void testGroupCapacityUsageSql() {
        assertUsageSql(new GroupCapacityMapperByMysql(), new GroupCapacityMapperByDaMeng(), Arrays.asList(
                GroupCapacityMapperByMysql::select, GroupCapacityMapperByMysql::insertIntoSelect,
                GroupCapacityMapperByMysql::insertIntoSelectByWhere, GroupCapacityMapperByMysql::incrementUsageByWhere,
                GroupCapacityMapperByMysql::incrementUsageByWhereQuotaEqualZero,
                GroupCapacityMapperByMysql::incrementUsageByWhereQuotaNotEqualZero, GroupCapacityMapperByMysql::decrementUsageByWhere,
                GroupCapacityMapperByMysql::updateUsage, GroupCapacityMapperByMysql::updateUsageByWhere));
    }

    @Test
    public void testTenantCapacityUsageSql() {
        assertUsageSql(new TenantCapacityMapperByMySql(), new TenantCapacityMapperByDaMeng(), Arrays.asList(
                TenantCapacityMapperByMySql::select, TenantCapacityMapperByMySql::insertTenantCapacity,
                TenantCapacityMapperByMySql::incrementUsage, TenantCapacityMapperByMySql::incrementUsageWithDefaultQuotaLimit,
                TenantCapacityMapperByMySql::incrementUsageWithQuotaLimit, TenantCapacityMapperByMySql::decrementUsage,
                TenantCapacityMapperByMySql::correctUsage));
    }

    private static <T> void assertUsageSql(T mysql, T dameng, List<BiFunction<T, MapperContext, MapperResult>> operations) {
        MapperContext context = new MapperContext();
        context.putWhereParameter(FieldConstant.GROUP_ID, "group");
        context.putWhereParameter(FieldConstant.TENANT_ID, "tenant");
        context.putWhereParameter(FieldConstant.USAGE, 2);
        for (BiFunction<T, MapperContext, MapperResult> operation : operations) {
            MapperResult mysqlResult = operation.apply(mysql, context);
            MapperResult damengResult = operation.apply(dameng, context);
            assertEquals(mysqlResult.getSql().replace("`usage`", FieldConstant.USAGE), damengResult.getSql());
            assertEquals(mysqlResult.getParamList(), damengResult.getParamList());
        }
    }
}
