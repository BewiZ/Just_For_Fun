let isCodeExit = false; // 用于判断是否有源代码

document.addEventListener('DOMContentLoaded', function () {
    hljs.configure({
        languages: ['html', 'javascript', 'css'], // 配置高亮显示的语言
    }); // 配置高亮显示

    // hljs.highlightAll();
    // hljs.initLineNumbersOnLoad();

    const urlInput = document.getElementById('url-input'); // 获取URL输入框
    const fetchButton = document.getElementById('fetch-button'); // 获取获取按钮
    const themeToggle = document.getElementById('theme-toggle'); // 获取主题切换按钮
    const copybtn = document.getElementById('copy-btn'); // 获取复制按钮
    const srcCode = document.getElementById('source-code'); // 获取源代码显示区域


    // 获取代码按钮
    fetchButton.addEventListener('click', async function () { // 添加点击事件监听器
        const url = urlInput.value.trim(); // 获取输入的URL并去除前后空格
        if (!url) { // 如果URL为空，则显示警告框
            alert('请输入URL！');
            return;
        }

        srcCode.textContent = ''; // 显示空

        try {
            // 使用代理绕过CORS限制
            const proxyUrl = 'https://api.allorigins.win/raw?url=';
            // 发送请求到代理服务器
            // await 用于等待后面的fetch函数完成并将结果存储在 response 中，若完不成，抛出错误
            // encodeURIComponent 函数会对传入的字符串进行遍历，将所有非字母数字字符以及某些保留字符（如 :, /, ?, @, &, =, +, $, , 等）转换为 UTF-8 编码，并用百分号（%）加上两位十六进制数表示。
            //例如，空格字符会被转换为 %20，中文字符会根据 UTF-8 编码转换为多个 % 加上两位十六进制数的形式。
            const response = await fetch(proxyUrl + encodeURIComponent(url)); // 发送请求
            if (!response.ok) { // 检查响应是否成功
                throw new Error('网络错误！状态码：' + response.status); // 如果响应不成功，抛出错误
            }

            const htmlContent = await response.text(); // 获取响应文本

            isCodeExit = true; // 源代码存在
            if (isCodeExit) {
                document.querySelectorAll('pre').forEach(pre => {
                    pre.style.padding = '8px 0px';
                });
            }

            srcCode.textContent = htmlContent; // 显示源代码

            // 高亮显示代码
            hljs.highlightElement(srcCode);
            // 添加行号
            hljs.lineNumbersBlock(srcCode);

        } catch (error) {
            // 在控制台显示完整错误信息
            console.error('获取失败：', error);
            // 在页面上显示错误信息
            srcCode.textContent = '获取源代码失败: ' + error.message;
        }

    })

    // 复制按钮
    copybtn.addEventListener('click', function () {

        const textArea = document.createElement('textarea'); // 创建临时textarea元素
        textArea.value = srcCode.textContent; // 将源代码内容赋值给textarea
        document.body.appendChild(textArea); // 将textarea添加到文档中
        textArea.select(); // 选中textarea中的文本
        document.execCommand('copy'); // 执行复制命令
        document.body.removeChild(textArea); // 移除临时textarea元素


        // 显示复制成功提示
        const oriText = copybtn.innerHTML; // 获取原始按钮文本
        copybtn.innerHTML = '<i class="fa-solid fa-check"></i>已复制'; // 修改按钮文本为复制成功提示
        setTimeout(function () {
            copybtn.innerHTML = oriText; // 2000ms后恢复原始按钮文本
        }, 2000);
    });






    // 主题切换按钮
    themeToggle.addEventListener('click', function () {
        const themeShow = document.getElementById('source-code');
        const icon = themeToggle.querySelector('i'); // 获取图标元素

        // toggle 方法用于切换类名，如果类名存在则删除，如果不存在则添加
        document.body.classList.toggle('dark-theme'); // 切换暗黑主题

        // 根据当前主题切换图标
        if (document.body.classList.contains('dark-theme')) {
            icon.classList.add('fa-sun');
            icon.classList.remove('fa-moon');
        } else {
            icon.classList.add('fa-moon');
            icon.classList.remove('fa-sun');
        }

        if (!isCodeExit) {
            themeShow.textContent = '已切换至' + (document.body.classList.contains('dark-theme') ? '暗黑' : '明亮') + '主题';
        }
    });
})
