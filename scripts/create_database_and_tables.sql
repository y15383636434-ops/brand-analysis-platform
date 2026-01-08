-- 创建品牌分析系统数据库和表
-- 完整脚本：创建数据库（如果不存在）+ 创建所有表

-- ========================================
-- 第一步：创建数据库
-- ========================================
CREATE DATABASE IF NOT EXISTS brand_analysis 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 选择数据库
USE brand_analysis;

-- ========================================
-- 第二步：创建表
-- ========================================

-- 创建brands表
CREATE TABLE IF NOT EXISTS brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    industry VARCHAR(100),
    website VARCHAR(255),
    logo_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建crawl_tasks表
CREATE TABLE IF NOT EXISTS crawl_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    keywords TEXT,
    max_items INT DEFAULT 100,
    include_comments BOOLEAN DEFAULT FALSE,
    celery_task_id VARCHAR(255),
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_status (status),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建analysis_tasks表
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    crawl_task_id INT,
    status VARCHAR(20) DEFAULT 'pending',
    analysis_type VARCHAR(50),
    celery_task_id VARCHAR(255),
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (crawl_task_id) REFERENCES crawl_tasks(id) ON DELETE SET NULL,
    INDEX idx_brand_id (brand_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建reports表
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    analysis_task_id INT,
    report_type VARCHAR(50),
    file_path VARCHAR(500),
    file_size BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_task_id) REFERENCES analysis_tasks(id) ON DELETE SET NULL,
    INDEX idx_brand_id (brand_id),
    INDEX idx_report_type (report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 第三步：显示创建结果
-- ========================================
SELECT '数据库和表创建完成！' AS message;
SHOW TABLES;








