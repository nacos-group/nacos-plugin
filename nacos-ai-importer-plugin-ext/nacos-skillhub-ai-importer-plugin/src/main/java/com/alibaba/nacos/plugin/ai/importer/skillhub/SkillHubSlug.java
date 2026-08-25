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
package com.alibaba.nacos.plugin.ai.importer.skillhub;

import com.alibaba.nacos.common.utils.StringUtils;

/**
 * SkillHub namespace / canonical slug helpers (ported from base_agent skillhub_slug).
 *
 * @author nacos
 */
public final class SkillHubSlug {
    
    private SkillHubSlug() {
    }
    
    public static String normalizeNamespace(String namespace) {
        String cleaned = namespace == null ? "" : namespace.trim();
        if (cleaned.startsWith("@")) {
            cleaned = cleaned.substring(1).trim();
        }
        return cleaned;
    }
    
    public static String hubCanonicalSlug(String namespace, String skillName) {
        String ns = normalizeNamespace(namespace);
        String name = skillName == null ? "" : skillName.trim();
        if (StringUtils.isBlank(ns) || StringUtils.isBlank(name)) {
            throw new IllegalArgumentException("namespace and skill_name are required");
        }
        if ("global".equals(ns)) {
            return name;
        }
        return ns + "--" + name;
    }
    
    public static String localSkillNameFromCanonical(String namespace, String canonicalSlug) {
        String ns = normalizeNamespace(namespace);
        String slug = canonicalSlug == null ? "" : canonicalSlug.trim();
        if (StringUtils.isBlank(slug)) {
            throw new IllegalArgumentException("canonical_slug is required");
        }
        if ("global".equals(ns)) {
            String prefix = "global--";
            if (slug.startsWith(prefix)) {
                return slug.substring(prefix.length());
            }
            return slug;
        }
        String prefix = ns + "--";
        if (slug.startsWith(prefix)) {
            return slug.substring(prefix.length());
        }
        if (!slug.contains("--")) {
            return slug;
        }
        int index = slug.indexOf("--");
        return slug.substring(index + 2);
    }
    
    public static boolean skillBelongsToNamespace(String namespace, String canonicalSlug) {
        String ns = normalizeNamespace(namespace);
        String slug = canonicalSlug == null ? "" : canonicalSlug.trim();
        if (StringUtils.isBlank(slug)) {
            return false;
        }
        if ("global".equals(ns)) {
            return !slug.contains("--") || slug.startsWith("global--");
        }
        return slug.startsWith(ns + "--");
    }
    
    /**
     * Parse search input into namespace + keyword.
     *
     * <p>Supported forms:
     * <ul>
     *   <li>{@code @team-x} → namespace=team-x, keyword empty</li>
     *   <li>{@code @team-x alpha} → namespace=team-x, keyword=alpha</li>
     *   <li>{@code @team-x/alpha} → namespace=team-x, keyword=alpha</li>
     *   <li>{@code team-x--alpha} → namespace=team-x, keyword=alpha</li>
     *   <li>{@code alpha} → namespace from defaultNamespace, keyword=alpha</li>
     * </ul>
     */
    public static NamespaceQuery parseSearchQuery(String rawQuery, String defaultNamespace) {
        String query = rawQuery == null ? "" : rawQuery.trim();
        if (query.startsWith("@")) {
            String body = query.substring(1).trim();
            if (StringUtils.isBlank(body)) {
                return new NamespaceQuery(normalizeNamespace(defaultNamespace), "");
            }
            int slash = indexOfNamespaceSeparator(body, '/');
            int space = indexOfNamespaceSeparator(body, ' ');
            int split = earliestPositive(slash, space);
            if (split > 0) {
                String ns = normalizeNamespace(body.substring(0, split));
                String keyword = body.substring(split + 1).trim();
                return new NamespaceQuery(ns, keyword);
            }
            return new NamespaceQuery(normalizeNamespace(body), "");
        }
        if (query.contains("--")) {
            int index = query.indexOf("--");
            String ns = normalizeNamespace(query.substring(0, index));
            String keyword = query.substring(index + 2).trim();
            if (StringUtils.isNotBlank(ns)) {
                return new NamespaceQuery(ns, keyword);
            }
        }
        return new NamespaceQuery(normalizeNamespace(defaultNamespace), query);
    }
    
    private static int indexOfNamespaceSeparator(String value, char separator) {
        int index = value.indexOf(separator);
        return index < 0 ? -1 : index;
    }
    
    private static int earliestPositive(int left, int right) {
        if (left < 0) {
            return right;
        }
        if (right < 0) {
            return left;
        }
        return Math.min(left, right);
    }
    
    /**
     * Namespace + remaining keyword from a search query.
     */
    public static final class NamespaceQuery {
        
        private final String namespace;
        
        private final String keyword;
        
        public NamespaceQuery(String namespace, String keyword) {
            this.namespace = namespace == null ? "" : namespace;
            this.keyword = keyword == null ? "" : keyword;
        }
        
        public String getNamespace() {
            return namespace;
        }
        
        public String getKeyword() {
            return keyword;
        }
    }
}
