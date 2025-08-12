# Nacos数据库适配插件

## 一、插件概述

### 1.1、简介

从Nacos2.2版本开始，Nacos提供了数据源扩展插件，以便让需要进行其他数据库适配的用户自己编写插件来保存数据。当前项目插件目前已简单适配Postgresql。

如需Nacos2.1支持，请移步个人的如下这个仓库：

https://github.com/wuchubuzai2018/nacos-multidatasource

当前项目基于Nacos2.2版本的扩展插件口进行开发。

### 2.2、插件工程结构说明

nacos-datasource-plugin-ext-base工程为数据库插件操作的适配抽象。

nacos-all-datasource-plugin-ext工程可打包所有适配的数据库插件

nacos-postgresql-datasource-plugin-ext工程可打包适配Postgresql的数据库插件

## 二、下载和使用

### 2.1、插件引入

- 方式一：使用postgresql作为依赖引入到Nacos主分支源码中，例如：

```xml
<dependency>
    <groupId>com.alibaba.nacos</groupId>
    <artifactId>nacos-postgresql-datasource-plugin-ext</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

- 方式二：下载当前插件项目源码，打包为jar包 将该文件的路径配置到startup.sh文件中，使用Nacos的loader.path机制指定该插件的路径，可修改startup.sh中的loader.path参数的位置进行指定。
- 默认情况下，startup.sh 脚本中已经指定了默认的插件路径 ${NACOS_HOME}/plugins
- 因此，可以将打包后的插件 jar 包放到此目录下
- 最终形成的目录结构如下

```shell
bin
  startup.sh
conf
  application.properties
target
  nacos-server.jar
plugins
```

- 因此，你要做的就是，将插件的 jar 包，以及包含依赖的 jar 包都放到 plugins 目录下即可
- 本 fork 分支下，我们提供数据源插件的打包的 jar 包，但是，这个 jar 包是不包含数据库的 JDBC 驱动的
- 因此，你除了将需要的数据源的 jar 包放到 plugins 目录下之外，还需要对应的 JDBC 的驱动 jar 包也放到下面去
  - 这样做的目的是为了将 JDBC 驱动进行解耦，以便于你可以选择自己更合适的 JDBC 驱动版本
  - 而不是插件里面直接合并的驱动版本
- 以 postgre 为例，你需要这两个 jar 包

```shell
nacos-postgresql-datasource-plugin-ext-1.0.0-SNAPSHOT.jar
postgresql-42.2.19.jar
```

- 因此，只需要将这两个 jar 包放到 plugins 目录下即可
- 然后就是更改 conf/application.properties 里面的配置为你的数据源即可

### 2.2、修改数据库配置文件

在application.properties文件中声明postgresql的配置信息：

```java
spring.datasource.platform=postgresql
db.url.0=jdbc:postgresql://127.0.0.1:5432/nacos?tcpKeepAlive=true&reWriteBatchedInserts=true&ApplicationName=nacos_java
db.user=nacos
db.password=nacos
db.pool.config.driverClassName=org.postgresql.Driver
#如果是 oracle 则需要改为 SELECT * FROM dual 
#db.pool.config.connectionTestQuery=SELECT 1
```

### 2.3、导入Postgresql的数据库脚本文件

导入nacos-postgresql的脚本文件，脚本文件在nacos-postgresql-datasource-plugin-ext/src/main/resources/schema文件夹下面.

上面操作完成后，启动Nacos即可。

## 三、其他数据库插件开发

可参考nacos-postgresql-datasource-plugin-ext工程，新创建Maven项目，实现AbstractDatabaseDialect类，重写相关的分页操作逻辑与方法，并创建相应的mapper实现。