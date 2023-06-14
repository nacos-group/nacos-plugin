# Nacos数据库适配插件-磐维

## 一、插件概述

### 1.1、简介

从Nacos2.2版本开始，Nacos提供了数据源扩展插件，以便让需要进行其他数据库适配的用户自己编写插件来保存数据。当前项目插件目前已简单适配磐维数据库。

如需Nacos2.1支持，请移步如下这个仓库：

https://github.com/wuchubuzai2018/nacos-multidatasource

当前项目基于Nacos2.2版本的扩展插件口进行开发。

### 2.2、插件工程结构说明

nacos-datasource-plugin-ext-base工程为数据库插件操作的适配抽象。

nacos-all-datasource-plugin-ext工程可打包所有适配的数据库插件

nacos-panwei-datasource-plugin-ext工程可打包适配磐维的数据库插件

## 二、下载和使用

### 2.1、插件引入

方式一：下载当前插件项目源码，打包为jar包，将该jar包与panweidb-jdbc-x.x.x.jar一起放入{nacos所在目录}/plugins下

### 2.2、修改数据库配置文件

在application.properties文件中声明panwei的配置信息：

```properties
spring.datasource.platform=panwei
db.url.0=jdbc:panweidb://127.0.0.1:17700/nacos
db.user.0=nacos
db.password.0=nacos
db.pool.config.driverClassName=org.panweidb.Driver
#如果是 oracle 则需要改为 SELECT * FROM dual
db.pool.config.connectionTestQuery=SELECT 1
```

### 2.3、导入panwei的数据库脚本文件

导入nacos-panwei的脚本文件，脚本文件在nacos-panwei-datasource-plugin-ext/src/main/resources/schema文件夹下面.

上面操作完成后，启动Nacos即可。

## 三、其他数据库插件开发

可参考nacos-panwei-datasource-plugin-ext工程，新创建Maven项目，实现AbstractDatabaseDialect类，重写相关的分页操作逻辑与方法，并创建相应的mapper实现。

## 四、 磐维数据库简介
“中国移动磐维数据库”（ChinaMobileDB），简称“磐维数据库”（CMDB）。
是中国移动信息技术中心首个基于中国本土开源数据库打造的面向ICT基础设施
的自研数据库产品。在 2022 年 12 月 29 日 openGauss 开源社区主办的 openGauss
Summit 2022 会议上正式发布。
其产品内核能力基于华为 OpenGauss 开源软件，并进一步提升系统稳定性。
目前完全支持 PostgreSQL 生态，具备 MySQL 常规兼容能力，磐维数据库将优先
用于 IT 领域 MySQL 替代。