package com.alibaba.nacos.plugin.datasource.enums;


import java.util.HashMap;
import java.util.Map;

/**
 * @BelongsProject: nacos-plugin
 * @BelongsPackage: com.alibaba.nacos.plugin.datasource.enums
 * @Author: xieyos
 * @CreateTime: 2026-01-04  17:15
 * 把通用函数名映射到 Kingbase 的实际 SQL 表达式（尽量使用 Kingbase/Postgres 等效函数）。
 * 只列出 Nacos 常用/需要的函数；如需扩展，往里加即可。
 * @Version: 1.0
 */

public enum TrustedKingbaseFunctionEnum {

    // 注意：右侧是 Kingbase 对应的 SQL 表达（可含 precision 等）
    NOW("NOW()", "CURRENT_TIMESTAMP(3)"),
    LENGTH("LENGTH", "LENGTH"),            // LENGTH(col)
    SUBSTR("SUBSTR", "SUBSTR"),            // SUBSTR(col, pos, len) 或 SUBSTRING
    COALESCE("IFNULL", "COALESCE"),        // 将 IFNULL 映射到 COALESCE
    CONCAT("CONCAT", "CONCAT"),            // CONCAT(a,b,...)
    CONCAT_WS("CONCAT_WS", "CONCAT_WS"),   // 如需实现可保留
    RANDOM("RAND", "RANDOM()"),            // RAND() -> RANDOM() (Postgres)
    LOWER("LOWER", "LOWER"),
    UPPER("UPPER", "UPPER");

    private static final Map<String, TrustedKingbaseFunctionEnum> LOOKUP = new HashMap<>();

    static {
        for (TrustedKingbaseFunctionEnum e : values()) {
            LOOKUP.put(e.functionName, e);
        }
    }

    private final String functionName;
    private final String function;

    TrustedKingbaseFunctionEnum(String functionName, String function) {
        this.functionName = functionName;
        this.function = function;
    }

    /**
     * 通过通用名获取对应的数据库函数字符串（用于直接拼 SQL）。
     * 如果找不到，抛出 IllegalArgumentException，调用方可捕捉处理。
     */
    public static String getFunctionByName(String functionName) {
        TrustedKingbaseFunctionEnum entry = LOOKUP.get(functionName);
        if (entry != null) {
            return entry.function;
        }
        throw new IllegalArgumentException(String.format("Invalid function name: %s", functionName));
    }
}

