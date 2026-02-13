package com.alibaba.nacos.plugin.datasource.enums.kingbase;

import java.util.HashMap;
import java.util.Map;

/**
 * The TrustedKingbaseFunctionEnum enum class is used to enumerate and manage a list of trusted built-in SQL functions.
 * By using this enum, you can verify whether a given SQL function is part of the trusted functions list
 * to avoid potential SQL injection risks.
 *
 * @author chunhai
 */
public enum TrustedKingbaseFunctionEnum {
    /**
     * NOW().
     */
    NOW("NOW()", "NOW()");

    private static final Map<String, TrustedKingbaseFunctionEnum> LOOKUP_MAP = new HashMap<>();

    static {
        for (TrustedKingbaseFunctionEnum entry : TrustedKingbaseFunctionEnum.values()) {
            LOOKUP_MAP.put(entry.functionName, entry);
        }
    }

    private final String functionName;

    private final String function;

    TrustedKingbaseFunctionEnum(String functionName, String function) {
        this.functionName = functionName;
        this.function = function;
    }

    /**
     * Get the function name.
     *
     * @param functionName function name
     * @return function
     */
    public static String getFunctionByName(String functionName) {
        TrustedKingbaseFunctionEnum entry = LOOKUP_MAP.get(functionName);
        if (entry != null) {
            return entry.function;
        }
        throw new IllegalArgumentException(String.format("Invalid function name: %s", functionName));
    }
}
