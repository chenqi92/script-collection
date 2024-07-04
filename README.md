> [!前言]
> 对于经常写笔记或者写文档得同学来说，经常会需要获取一个项目工程下得目录结构，那么如何在不需要下载或者安装插件来达到这个目的呢？
## 示例
### 只含有三级目录
![](https://nas.allbs.cn:9006/cloudpic/2024/06/0747c8da143ff01f80da254578b46db4.png)
### 包含文件得四级文件树
![](https://nas.allbs.cn:9006/cloudpic/2024/06/790860951e8f44124360cc9fe572c4e2.png)
### 指定忽略部分文件或者文件夹，比如target目录，logs目录
![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/1395e2d07c09d65961754d4a0ab422cb.png)
## 使用方法
### 双击`tree.sh`运行
运行过程中会有需要交互得地方
#### 是否应用 .gitignore 中的内容?
我们知道git提交会配置.gitignore来忽略不想提交得内容，spring boot中得target目录、logs目录等，前端得.vscode目录等，我们并不想将这些内容输出到文件树中，就在第一个用户交互得地方输入`y`。

![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/00db999f7f3195ca10617d84476c4da1.png)
#### 输出的树是否不包含文件?

如果输入`y`则会将所有文件输出到结果得树中。

![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/ed42f9a7596c740c5abfe0e01aa49fd2.png)
#### 请输入输出的层级 (默认输出所有层级):

默认为所有层级，输入数字则输出数字对应得层级

![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/cdf7ff057a17f1b3e4786c939319b9a9.png)
#### 是否导出这个输出的树? (y/n)

最后是导出这个树到txt文件中，便于复制使用

![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/874888a177d68eba408919fc7e184ac7.png)

![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/906183764eb52c7254ce16c58884a46d.png)

![image.png](https://nas.allbs.cn:9006/cloudpic/2024/06/7e398962862d6e38a4723f3fea3e1004.png)
