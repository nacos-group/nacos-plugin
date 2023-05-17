/*
 * Copyright 1999-2021 Alibaba Group Holding Ltd.
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

package com.alibaba.nacos.plugin.config;

import java.io.Serializable;

/**
 * @authorliyunfei
 * @date2023/1/7
 **/
public class ConfigChangeNotifyInfo implements Serializable {

    private static final Long serialVersionUID = 19202931239213L;

    /**
     * Value of {@link com.alibaba.nacos.plugin.config.constants.ConfigChangePointCutTypes}.
     */
    private String action;

    /**
     * The result of handle.
     */
    private Boolean rs;

    /**
     * Time of config change.
     */
    private String modifyTime;

    private String errorMsg;

    private String dataId;

    private String group;

    private String tenant;

    private String content;

    private String srcIp;

    private String srcUser;

    private String use;

    private String appName;

    private String effect;

    private String type;

    private String desc;

    private String tag;

    private String configTags;

    private String namespace;

    public ConfigChangeNotifyInfo(String action, Boolean rs, String modifyTime) {
        this.action = action;
        this.rs = rs;
        this.modifyTime = modifyTime;
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }

    public Boolean getRs() {
        return rs;
    }

    public void setRs(Boolean rs) {
        this.rs = rs;
    }

    public String getModifyTime() {
        return modifyTime;
    }

    public void setModifyTime(String modifyTime) {
        this.modifyTime = modifyTime;
    }

    public String getErrorMsg() {
        return errorMsg;
    }

    public void setErrorMsg(String errorMsg) {
        this.errorMsg = errorMsg;
    }

    public String getDataId() {
        return dataId;
    }

    public void setDataId(String dataId) {
        this.dataId = dataId;
    }

    public String getGroup() {
        return group;
    }

    public void setGroup(String group) {
        this.group = group;
    }

    public String getTenant() {
        return tenant;
    }

    public void setTenant(String tenant) {
        this.tenant = tenant;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getSrcIp() {
        return srcIp;
    }

    public void setSrcIp(String srcIp) {
        this.srcIp = srcIp;
    }

    public String getSrcUser() {
        return srcUser;
    }

    public void setSrcUser(String srcUser) {
        this.srcUser = srcUser;
    }

    public String getUse() {
        return use;
    }

    public void setUse(String use) {
        this.use = use;
    }

    public String getAppName() {
        return appName;
    }

    public void setAppName(String appName) {
        this.appName = appName;
    }

    public String getEffect() {
        return effect;
    }

    public void setEffect(String effect) {
        this.effect = effect;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getDesc() {
        return desc;
    }

    public void setDesc(String desc) {
        this.desc = desc;
    }

    public String getTag() {
        return tag;
    }

    public void setTag(String tag) {
        this.tag = tag;
    }

    public String getConfigTags() {
        return configTags;
    }

    public void setConfigTags(String configTags) {
        this.configTags = configTags;
    }

    public String getNamespace() {
        return namespace;
    }

    public void setNamespace(String namespace) {
        this.namespace = namespace;
    }

    @Override
    public String toString() {
        return "ConfigChangeNotifyInfo{" + "action='" + action + '\'' + ", rs=" + rs + ", modifyTime='" + modifyTime
                + '\'' + ", errorMsg='" + errorMsg + '\'' + ", dataId='" + dataId + '\'' + ", group='" + group + '\''
                + ", tenant='" + tenant + '\'' + ", content='" + content + '\'' + ", srcIp='" + srcIp + '\''
                + ", srcUser='" + srcUser + '\'' + ", use='" + use + '\'' + ", appName='" + appName + '\''
                + ", effect='" + effect + '\'' + ", type='" + type + '\'' + ", desc='" + desc + '\'' + ", tag='" + tag
                + '\'' + ", configTags='" + configTags + '\'' + ", namespace='" + namespace + '}';
    }
}

