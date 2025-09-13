// 页面和导航元素
const pages = {
    indexManager: document.getElementById('indexManagerPage'),
    createIndex: document.getElementById('createIndexPage'),
    indexDetail: document.getElementById('indexDetailPage'),
    search: document.getElementById('searchPage'),
    videoDetail: document.getElementById('videoDetailPage')
};

const navButtons = {
    indexManager: document.getElementById('indexManagerBtn'),
    search: document.getElementById('searchBtn')
};

// 视频详情分页相关变量
let currentVideoPath = null;
let currentVideoPage = 1;
let currentVideoTotalPages = 0;

// 当前状态
let currentIndex = null;
let selectedFiles = [];

// 分页相关变量
const PAGE_SIZE = 10;
let currentPage = 1;
let totalPages = 0;
let allIndexes = [];

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    // 设置导航按钮事件
    navButtons.indexManager.addEventListener('click', () => showPage('indexManager'));
    navButtons.search.addEventListener('click', () => showPage('search'));
    
    // 设置创建索引页面的事件
    document.getElementById('createIndexBtn').addEventListener('click', () => showPage('createIndex'));
    document.getElementById('backToIndexManager').addEventListener('click', () => showPage('indexManager'));
    document.getElementById('cancelCreateBtn').addEventListener('click', () => showPage('indexManager'));
    document.getElementById('selectFilesBtn').addEventListener('click', handleFileSelect);
    document.getElementById('createIndexForm').addEventListener('submit', createIndex);
    
    // 设置索引详情页面的事件
    document.getElementById('backToIndexList').addEventListener('click', () => showPage('indexManager'));
    document.getElementById('searchInIndexBtn').addEventListener('click', () => showPage('search'));
    
    // 设置搜索页面的事件
    document.getElementById('backToIndexDetail').addEventListener('click', () => showPage('indexDetail'));
    document.getElementById('searchForm').addEventListener('submit', performSearch);
    
    // 初始加载索引列表
    loadIndexList();
    
    // 显示默认页面
    showPage('indexManager');
    
    // 设置索引详情页面的删除按钮事件
    document.getElementById('deleteIndexBtn').addEventListener('click', deleteIndex);
    
    // 设置索引详情页面的添加视频按钮事件
    document.getElementById('addVideoBtn').addEventListener('click', addVideoFiles);
});

// 页面导航函数
function showPage(pageName) {
    // 隐藏所有页面
    Object.values(pages).forEach(page => {
        page.classList.remove('active');
    });
    
    // 显示请求的页面
    pages[pageName].classList.add('active');
    
    // 更新导航按钮状态
    Object.values(navButtons).forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (pageName === 'indexManager' || pageName === 'createIndex' || pageName === 'indexDetail' || pageName === 'videoDetail') {
        navButtons.indexManager.classList.add('active');
    } else if (pageName === 'search') {
        navButtons.search.classList.add('active');
    }
    
    // 根据页面执行特定操作
    if (pageName === 'indexManager') {
        loadIndexList();
    } else if (pageName === 'createIndex') {
        resetCreateIndexForm();
    } else if (pageName === 'indexDetail' && currentIndex) {
        loadIndexDetail(currentIndex);
    } else if (pageName === 'search' && currentIndex) {
        // 初始化搜索页面
        initializeSearchPage();
    } else if (pageName === 'videoDetail' && currentIndex && currentVideoPath) {
        // 初始化视频详情页面
        initializeVideoDetailPage();
    }
}

// 初始化视频详情页面
function initializeVideoDetailPage() {
    // 显示当前索引名称
    const indexNameElement = document.getElementById('currentVideoIndexName');
    if (indexNameElement && currentIndex) {
        indexNameElement.textContent = currentIndex.name;
    }
    
    // 显示当前视频路径
    const videoPathElement = document.getElementById('currentVideoPath');
    if (videoPathElement && currentVideoPath) {
        videoPathElement.textContent = currentVideoPath;
    }
    
    // 加载视频详情
    loadVideoDetail(currentVideoPage);
}

// 获取状态文本
function getStatusText(status) {
    switch (status) {
        case "waiting": return '待处理';
        case 'processing': return '处理中';
        case 'completed': return '已完成';
        case 'error': return '错误';
        default: return '未知';
    }
}

// 重置创建索引表单
function resetCreateIndexForm() {
    document.getElementById('indexName').value = '';
    selectedFiles = [];
    updateFileList();
}

// 处理文件选择
async function handleFileSelect(event) {
    const { ipcRenderer } = window.require('electron');
    const filePaths = await ipcRenderer.invoke('open-file-dialog');
    if (filePaths && filePaths.length > 0) {
        // 将文件路径转换为包含name属性的对象
        const newFiles = filePaths.map(path => ({
            path: path,
            name: path.split('/').pop().split('\\').pop() // 提取文件名
        }));
        selectedFiles = [...selectedFiles, ...newFiles];
        updateFileList();
    }
}

// 显示消息函数
function showMessage(message, type) {
    // 获取消息容器
    const messageContainer = document.getElementById('messageContainer');
    
    // 移除之前的消息元素
    const existingMessage = messageContainer.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;
    messageElement.textContent = message;
    
    // 添加样式
    messageElement.style.position = 'fixed';
    messageElement.style.top = '20px';
    messageElement.style.left = '50%';
    messageElement.style.transform = 'translateX(-50%)';
    messageElement.style.padding = '10px 20px';
    messageElement.style.borderRadius = '4px';
    messageElement.style.color = 'white';
    messageElement.style.fontWeight = 'bold';
    messageElement.style.zIndex = '1000';
    messageElement.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    messageElement.style.transition = 'opacity 0.3s ease';
    
    // 根据消息类型设置背景颜色
    if (type === 'error') {
        messageElement.style.backgroundColor = '#dc3545';
    } else if (type === 'success') {
        messageElement.style.backgroundColor = '#28a745';
    } else {
        messageElement.style.backgroundColor = '#007bff';
    }
    
    // 添加到消息容器
    messageContainer.appendChild(messageElement);
    
    // 3秒后自动移除消息
    setTimeout(() => {
        messageElement.style.opacity = '0';
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }, 3000);
}

// 更新文件列表显示
function updateFileList() {
    const fileListContainer = document.getElementById('fileList');
    
    if (selectedFiles.length === 0) {
        fileListContainer.innerHTML = '<div class="empty-state"><p>未选择任何文件</p></div>';
        return;
    }
    
    fileListContainer.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>${file.name}</span>
            <button class="remove-file-btn" data-index="${index}">移除</button>
        `;
        fileListContainer.appendChild(fileItem);
    });
    
    // 添加移除按钮事件
    document.querySelectorAll('.remove-file-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.getAttribute('data-index'));
            selectedFiles.splice(index, 1);
            updateFileList();
        });
    });
}

// 显示搜索结果区域加载指示器
function showSearchLoading() {
    const searchResults = document.getElementById('searchResults');
    const searchLoadingIndicator = document.getElementById('searchLoadingIndicator');
    const searchResultsTable = searchResults.querySelector('.table');
    const noResults = document.getElementById('noResults');
    
    // 隐藏表格和无结果提示
    if (searchResultsTable) {
        searchResultsTable.style.display = 'none';
    }
    noResults.style.display = 'none';
    
    // 显示加载指示器
    searchLoadingIndicator.style.display = 'flex';
}

// 隐藏搜索结果区域加载指示器
function hideSearchLoading() {
    const searchResults = document.getElementById('searchResults');
    const searchLoadingIndicator = document.getElementById('searchLoadingIndicator');
    const searchResultsTable = searchResults.querySelector('.table');
    
    // 隐藏加载指示器
    searchLoadingIndicator.style.display = 'none';
    
    // 显示表格
    if (searchResultsTable) {
        searchResultsTable.style.display = 'table';
    }
}

// API 调用函数
const API_BASE = 'http://localhost:5001/api';

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }
        
        return data;
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

// 加载索引列表
async function loadIndexList() {
    try {
        const indexes = await apiCall('/indexes');
        allIndexes = indexes;
        totalPages = Math.ceil(indexes.length / PAGE_SIZE);
        
        // 显示当前页的索引
        displayIndexesForPage(currentPage);
        
        // 更新分页控件
        updatePagination();
    } catch (error) {
        console.error('加载索引列表失败:', error);
        document.getElementById('indexList').innerHTML = '<div class="empty-state"><p>加载数据失败</p></div>';
    }
}

// 显示指定页的索引
function displayIndexesForPage(page) {
    const indexListContainer = document.getElementById('indexList');
    const startIndex = (page - 1) * PAGE_SIZE;
    const endIndex = startIndex + PAGE_SIZE;
    const indexesToShow = allIndexes.slice(startIndex, endIndex);
    
    if (indexesToShow.length === 0) {
        indexListContainer.innerHTML = '<div class="empty-state"><p>暂无索引数据</p></div>';
        return;
    }
    
    indexListContainer.innerHTML = '';
    indexesToShow.forEach(index => {
        const indexCard = document.createElement('div');
        indexCard.className = 'index-card';
        indexCard.innerHTML = `
            <h3>${index.name}</h3>
            <div class="info-grid">
                <div class="info-item">
                    <span class="label">创建时间:</span>
                    <span class="value">${index.createDate}</span>
                </div>
                <div class="info-item">
                    <span class="label">索引状态:</span>
                    <span class="value status-${index.status}">${getStatusText(index.status)}</span>
                </div>
            </div>
            <div class="index-card-actions">
                <button class="btn-secondary delete-index-btn" data-index-id="${index.id}">删除索引</button>
            </div>
        `;
        indexCard.addEventListener('click', (event) => {
            // 检查点击的是否是删除按钮
            if (event.target.classList.contains('delete-index-btn')) {
                return;
            }
            currentIndex = index;
            showPage('indexDetail');
        });
        indexListContainer.appendChild(indexCard);
    });
    
    // 添加删除按钮事件
    document.querySelectorAll('.delete-index-btn').forEach(btn => {
        btn.addEventListener('click', async function(event) {
            event.stopPropagation(); // 阻止事件冒泡到索引卡片
            const indexId = this.getAttribute('data-index-id');
            
            // 确认删除
            if (!confirm('确定要删除这个索引吗？此操作不可恢复。')) {
                return;
            }
            
            try {
                await apiCall(`/indexes/${indexId}`, {
                    method: 'DELETE'
                });
                
                showMessage('索引删除成功', 'success');
                
                // 重新加载索引列表
                await loadIndexList();
                
                // 如果当前显示的是被删除索引的详情页面，返回到索引管理页面
                if (currentIndex && currentIndex.id === indexId) {
                    showPage('indexManager');
                    currentIndex = null;
                }
            } catch (error) {
                showMessage(`删除索引失败: ${error.message}`, 'error');
            }
        });
    });
}

// 更新分页控件
function updatePagination() {
    const paginationElement = document.getElementById('pagination');
    const pageInfoElement = document.getElementById('pageInfo');
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const pageJumpInput = document.getElementById('pageJumpInput');
    const pageJumpBtn = document.getElementById('pageJumpBtn');
    
    if (totalPages <= 1) {
        paginationElement.style.display = 'none';
        return;
    }
    
    paginationElement.style.display = 'flex';
    pageInfoElement.textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;
    
    // 更新按钮状态
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === totalPages;
    
    // 设置页码输入框的范围和当前值
    pageJumpInput.min = 1;
    pageJumpInput.max = totalPages;
    pageJumpInput.value = '';
    
    // 添加事件监听器（如果还没有添加）
    if (!prevButton.hasEventListener) {
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                displayIndexesForPage(currentPage);
                updatePagination();
            }
        });
        prevButton.hasEventListener = true;
    }
    
    if (!nextButton.hasEventListener) {
        nextButton.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                displayIndexesForPage(currentPage);
                updatePagination();
            }
        });
        nextButton.hasEventListener = true;
    }
    
    // 添加页码跳转事件监听器（如果还没有添加）
    if (!pageJumpBtn.hasEventListener) {
        pageJumpBtn.addEventListener('click', () => {
            const targetPage = parseInt(pageJumpInput.value);
            if (targetPage && targetPage >= 1 && targetPage <= totalPages && targetPage !== currentPage) {
                currentPage = targetPage;
                displayIndexesForPage(currentPage);
                updatePagination();
            }
        });
        pageJumpBtn.hasEventListener = true;
    }
    
    // 添加回车键跳转支持
    if (!pageJumpInput.hasEventListener) {
        pageJumpInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                pageJumpBtn.click();
            }
        });
        pageJumpInput.hasEventListener = true;
    }
}

// 创建索引
async function createIndex(event) {
    event.preventDefault();
    
    const indexName = document.getElementById('indexName').value.trim();
    
    if (!indexName) {
        showMessage('请输入索引名称', 'error');
        return;
    }
    
    if (selectedFiles.length === 0) {
        showMessage('请选择至少一个视频文件', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/indexes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: indexName,
                filePaths: selectedFiles.map(file => file.path)
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }
        
        showMessage(`索引 "${indexName}" 创建成功！`, 'success');
        currentIndex = data;
        showPage('indexDetail');
    } catch (error) {
        showMessage(`创建索引失败: ${error.message}`, 'error');
    }
}

// 加载索引详情
async function loadIndexDetail(index) {
    if (!index) return;
    
    try {
        const indexDetail = await apiCall(`/indexes/${index.id}`);
        
        // 更新基本信息
        document.getElementById('detailIndexName').textContent = indexDetail.name;
        document.getElementById('detailCreateDate').textContent = indexDetail.createDate;
        document.getElementById('detailIndexStatus').textContent = getStatusText(indexDetail.status);
        document.getElementById('detailIndexStatus').className = `value status-${indexDetail.status}`;
        
        // 更新视频文件列表
        const videoTableBody = document.getElementById('videoTableBody');
        videoTableBody.innerHTML = '';
        
        // 如果有文件数据，则显示文件列表
        if (indexDetail.files && indexDetail.files.length > 0) {
            indexDetail.files.forEach(file => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${file.path}</td>
                    <td class="status-${file.status}">${getStatusText(file.status)}</td>
                    <td>
                        <button class="btn-secondary view-details-btn" data-path="${file.path}">查看</button>
                        <button class="btn-secondary view-video-btn" data-path="${file.path}">打开</button>
                        <button class="btn-secondary delete-video-btn" data-path="${file.path}">删除</button>
                    </td>
                `;
                videoTableBody.appendChild(row);
            });
            
            // 添加查看按钮事件
            document.querySelectorAll('.view-details-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const filePath = this.getAttribute('data-path');
                    // 设置当前视频路径和页面
                    currentVideoPath = filePath;
                    currentVideoPage = 1;
                    // 跳转到视频详情页面
                    showPage('videoDetail');
                });
            });
            
            // 添加打开按钮事件
            document.querySelectorAll('.view-video-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const filePath = this.getAttribute('data-path');
                    const { shell } = window.require('electron');
                    shell.openPath(filePath);
                });
            });
            
            // 添加删除按钮事件
            document.querySelectorAll('.delete-video-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const filePath = this.getAttribute('data-path');
                    await deleteVideoFile(filePath);
                });
            });
        } else {
            // 如果没有文件数据，显示空状态
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="3" class="empty-state">暂无视频文件</td>';
            videoTableBody.appendChild(row);
        }
    } catch (error) {
        console.error('加载索引详情失败:', error);
        document.getElementById('videoTableBody').innerHTML = '<tr><td colspan="3" class="empty-state">加载数据失败</td></tr>';
    }
}

// 初始化搜索页面
function initializeSearchPage() {
    // 显示当前索引名称
    const indexNameElement = document.getElementById('currentSearchIndexName');
    if (indexNameElement && currentIndex) {
        indexNameElement.textContent = currentIndex.name;
    }
    
    // 清空搜索表单
    document.getElementById('searchQuery').value = '';
    document.getElementById('searchKeyword').value = '';
    document.getElementById('searchLimit').value = '10';
    
    // 填充视频选择下拉框，只显示索引成功的视频
    const videoSelect = document.getElementById('searchVideos');
    videoSelect.innerHTML = '';
    
    if (currentIndex && currentIndex.files) {
        // 过滤出状态为"completed"的文件
        const completedFiles = currentIndex.files.filter(file => file.status === 'completed');
        
        completedFiles.forEach(file => {
            const option = document.createElement('option');
            option.value = file.path;
            option.textContent = file.path;
            videoSelect.appendChild(option);
        });
    }
}

// 执行搜索
async function performSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('searchQuery').value.trim();
    const keyword = document.getElementById('searchKeyword').value.trim();
    const limit = parseInt(document.getElementById('searchLimit').value) || 10;
    
    // 获取选中的视频路径
    const videoSelect = document.getElementById('searchVideos');
    const selectedOptions = Array.from(videoSelect.selectedOptions);
    const videoPaths = selectedOptions.map(option => option.value);
    
    // 文本搜索是必须填写的
    if (!query) {
        showMessage('请输入搜索文本', 'error');
        return;
    }
    
    if (!currentIndex) {
        showMessage('请先选择一个索引', 'error');
        return;
    }
    
    // 显示搜索结果区域加载指示器
    showSearchLoading();
    
    // 构造搜索参数
    const searchParams = {
        nResults: limit,
        query: query
    };
    
    if (keyword) {
        searchParams.keyword = keyword;
    }
    
    if (videoPaths.length > 0) {
        searchParams.videoPaths = videoPaths;
    }
    
    try {
        const results = await apiCall(`/indexes/${currentIndex.id}/search`, {
            method: 'POST',
            body: JSON.stringify(searchParams)
        });
        
        displaySearchResults(results);
        showMessage('搜索完成', 'success');
    } catch (error) {
        showMessage(`搜索失败: ${error.message}`, 'error');
    } finally {
        // 隐藏搜索结果区域加载指示器
        hideSearchLoading();
    }
}

// 删除索引
async function deleteIndex() {
    if (!currentIndex) return;
    
    // 确认删除
    if (!confirm('确定要删除这个索引吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        await apiCall(`/indexes/${currentIndex.id}`, {
            method: 'DELETE'
        });
        
        showMessage('索引删除成功', 'success');
        
        // 返回到索引管理页面
        showPage('indexManager');
        currentIndex = null;
    } catch (error) {
        showMessage(`删除索引失败: ${error.message}`, 'error');
    }
}

// 添加视频文件
async function addVideoFiles() {
    if (!currentIndex) return;
    
    try {
        const { ipcRenderer } = window.require('electron');
        const filePaths = await ipcRenderer.invoke('open-file-dialog');
        
        if (filePaths && filePaths.length > 0) {
            // 显示加载指示器
            showSearchLoading();
            
            // 向索引中添加文件
            const response = await fetch(`${API_BASE}/indexes/${currentIndex.id}/files`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filePaths: filePaths
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '请求失败');
            }
            
            showMessage('文件添加成功', 'success');
            
            // 重新加载索引详情
            await loadIndexDetail(currentIndex);
        }
    } catch (error) {
        showMessage(`添加文件失败: ${error.message}`, 'error');
    } finally {
        // 隐藏加载指示器
        hideSearchLoading();
    }
}

// 删除视频文件
async function deleteVideoFile(filePath) {
    if (!currentIndex) return;
    
    // 确认删除
    if (!confirm('确定要删除这个视频文件吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        // 从索引中删除文件
        await apiCall(`/indexes/${currentIndex.id}/files/${encodeURIComponent(filePath)}`, {
            method: 'DELETE'
        });
        
        showMessage('文件删除成功', 'success');
        
        // 重新加载索引详情
        await loadIndexDetail(currentIndex);
    } catch (error) {
        showMessage(`删除文件失败: ${error.message}`, 'error');
    }
}

// 显示搜索结果
function displaySearchResults(results) {
    const resultsBody = document.getElementById('searchResultsBody');
    const noResults = document.getElementById('noResults');
    
    if (results.length === 0) {
        resultsBody.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    resultsBody.innerHTML = '';
    
    results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.videoPath}</td>
            <td>${result.startTime}</td>
            <td>${result.text}</td>
            <td><button class="btn-secondary play-video-btn" data-path="${result.videoPath}" data-time="${result.startTime}">播放</button></td>
        `;
        resultsBody.appendChild(row);
    });
    
    // 添加播放按钮事件
    document.querySelectorAll('.play-video-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filePath = this.getAttribute('data-path');
            const startTime = this.getAttribute('data-time');
            playVideoAtTime(filePath, startTime);
        });
    });
}


// 格式化时间显示
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

}



// 加载视频详情
async function loadVideoDetail(page) {
    if (!currentIndex || !currentVideoPath) return;
    
    // 显示加载指示器
    const loadingIndicator = document.getElementById('videoDetailLoadingIndicator');
    const resultsBody = document.getElementById('videoDetailResultsBody');
    const noResults = document.getElementById('videoDetailNoResults');
    const pagination = document.getElementById('videoDetailPagination');
    
    loadingIndicator.style.display = 'flex';
    resultsBody.style.display = 'none';
    noResults.style.display = 'none';
    pagination.style.display = 'none';
    
    try {
        // 构造请求参数
        const params = {
            filePath: currentVideoPath,
            page: page,
            pageSize: 100
        };
        
        const data = await apiCall(`/indexes/${currentIndex.id}/video/details`, {
            method: 'POST',
            body: JSON.stringify(params)
        });
        
        // 更新分页信息
        currentVideoPage = data.page;
        currentVideoTotalPages = data.total_pages;
        
        // 显示结果
        if (data.results && data.results.length > 0) {
            resultsBody.innerHTML = '';
            data.results.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${formatTime(item.start)}</td>
                    <td>${formatTime(item.end)}</td>
                    <td>${item.text}</td>
                    <td><button class="btn-secondary play-btn" data-time="${formatTime(item.start)}">播放</button></td>
                `;
                resultsBody.appendChild(tr);
            });
            
            // 添加播放按钮事件
            resultsBody.querySelectorAll('.play-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    playVideoAtTime(currentVideoPath, this.getAttribute('data-time'));
                });
            });
            
            resultsBody.style.display = 'table-row-group';
            noResults.style.display = 'none';
        } else {
            // 如果没有结果，显示提示信息
            resultsBody.innerHTML = '';
            resultsBody.style.display = 'none';
            noResults.style.display = 'block';
        }
        
        // 更新分页控件
        updateVideoDetailPagination();
        
        // 显示分页控件
        if (currentVideoTotalPages > 1) {
            pagination.style.display = 'flex';
        }
    } catch (error) {
        console.error('加载视频详情失败:', error);
        resultsBody.innerHTML = '<tr><td colspan="4" class="empty-state">加载数据失败</td></tr>';
        resultsBody.style.display = 'table-row-group';
        noResults.style.display = 'none';
    } finally {
        // 隐藏加载指示器
        loadingIndicator.style.display = 'none';
    }
}

// 更新视频详情分页控件
function updateVideoDetailPagination() {
    const pageInfoElement = document.getElementById('videoDetailPageInfo');
    const prevButton = document.getElementById('videoDetailPrevPage');
    const nextButton = document.getElementById('videoDetailNextPage');
    const pageJumpInput = document.getElementById('videoDetailPageJumpInput');
    const pageJumpBtn = document.getElementById('videoDetailPageJumpBtn');
    
    if (currentVideoTotalPages <= 1) {
        document.getElementById('videoDetailPagination').style.display = 'none';
        return;
    }
    
    document.getElementById('videoDetailPagination').style.display = 'flex';
    pageInfoElement.textContent = `第 ${currentVideoPage} 页，共 ${currentVideoTotalPages} 页`;
    
    // 更新按钮状态
    prevButton.disabled = currentVideoPage === 1;
    nextButton.disabled = currentVideoPage === currentVideoTotalPages;
    
    // 设置页码输入框的范围和当前值
    pageJumpInput.min = 1;
    pageJumpInput.max = currentVideoTotalPages;
    pageJumpInput.value = '';
    
    // 添加页码跳转事件监听器（如果还没有添加）
    if (!pageJumpBtn.hasEventListener) {
        pageJumpBtn.addEventListener('click', () => {
            const targetPage = parseInt(pageJumpInput.value);
            if (targetPage && targetPage >= 1 && targetPage <= currentVideoTotalPages && targetPage !== currentVideoPage) {
                loadVideoDetail(targetPage);
            }
        });
        pageJumpBtn.hasEventListener = true;
    }
    
    // 添加回车键跳转支持
    if (!pageJumpInput.hasEventListener) {
        pageJumpInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                pageJumpBtn.click();
            }
        });
        pageJumpInput.hasEventListener = true;
    }
}

// 添加视频详情页面的事件处理
document.addEventListener('DOMContentLoaded', function() {
    console.log('开始绑定视频详情页面事件');  // 调试信息
    
    // 分页按钮事件处理
    const videoDetailPrevPage = document.getElementById('videoDetailPrevPage');
    const videoDetailNextPage = document.getElementById('videoDetailNextPage');
    
    console.log('上一页按钮元素:', videoDetailPrevPage);  // 调试信息
    console.log('下一页按钮元素:', videoDetailNextPage);  // 调试信息
    
    if (videoDetailPrevPage) {
        videoDetailPrevPage.addEventListener('click', function() {
            console.log('点击上一页按钮');  // 调试信息
            if (currentVideoPage > 1) {
                loadVideoDetail(currentVideoPage - 1);
            }
        });
    }
    
    if (videoDetailNextPage) {
        videoDetailNextPage.addEventListener('click', function() {
            console.log('点击下一页按钮');  // 调试信息
            console.log('当前页:', currentVideoPage);  // 调试信息
            console.log('总页数:', currentVideoTotalPages);  // 调试信息
            if (currentVideoPage < currentVideoTotalPages) {
                loadVideoDetail(currentVideoPage + 1);
            }
        });
    }
    
    // 返回索引详情按钮事件处理
    const backToIndexDetailFromVideo = document.getElementById('backToIndexDetailFromVideo');
    console.log('返回索引详情按钮元素:', backToIndexDetailFromVideo);  // 调试信息
    
    if (backToIndexDetailFromVideo) {
        backToIndexDetailFromVideo.addEventListener('click', function() {
            console.log('点击返回索引详情按钮');  // 调试信息
            showPage('indexDetail');
        });
    } else {
        console.log('未找到返回索引详情按钮元素');  // 调试信息
    }
    
    console.log('视频详情页面事件绑定完成');  // 调试信息
});

function playVideoAtTime(filePath, startTime) {
    // 这里需要根据不同的操作系统和视频播放器来实现
    // 由于Electron的shell.openPath不支持传递参数，我们需要使用child_process来执行命令
    const { exec } = window.require('child_process');
    const { platform } = window.require('process');
    
    // 将时间格式转换为秒数
    const timeParts = startTime.split(':');
    const seconds = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60 + parseInt(timeParts[2]);
    
    // 根据不同操作系统构建命令
    let command;
    if (platform === 'win32' || platform === 'win64') {
        // Windows系统使用PotPlayer播放器
        command = `PotPlayerMini64.exe "${filePath}" /seek=${seconds}`;
    } else if (platform === 'darwin') {
        // macOS系统使用PotPlayer播放器（如果已安装）
        command = `open -a PotPlayer --args "${filePath}" /seek=${seconds}`;
    } else {
        // Linux系统使用PotPlayer播放器（如果已安装）
        command = `potplayer "${filePath}" /seek=${seconds}`;
    }
    
    // 执行命令
    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`执行命令时出错: ${error}`);
            alert(`无法播放视频文件: ${filePath}\n请确保已安装PotPlayer播放器，错误： ${error}`);
            return;
        }
        if (stderr) {
            console.error(`命令执行出错: ${stderr}`);
        }
    });
}
