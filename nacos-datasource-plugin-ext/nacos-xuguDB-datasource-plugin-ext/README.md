# Nacos数据库 xuguDB适配插件

## 一、注意事项

### 1.1、修改数据库配置文件

在application.properties文件中声明 xuguDB的配置信息：

```properties
spring.datasource.platform=xugu
db.url.0=jdbc:xugu://127.0.0.1:5137/SYSTEM?current_schema=nacos_database
db.user.0=SYSDBA
db.password.0=SYSDBA
db.pool.config.driverClassName=com.xugu.cloudjdbc.Driver
```

### 1.2、增加xuguDB数据库驱动


```xml
  <dependency>
    <groupId>com.xugudb</groupId>
    <artifactId>xugu-jdbc</artifactId>
    <version>12.3.5</version>
</dependency>
```

### 1.3、表结构初始化

在nacos数据库中执行schema/nacos-xugu.sql文件
````