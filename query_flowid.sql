-- 验证出库单 ROA20260304005 批次号 25252 的扣杂重量分配算法
-- 检查是否存在扣杂重量分配错误的问题

-- 1. 查询出库单主表信息
SELECT 
    '出库单主表信息' AS 查询类型,
    wsof.OUT_NO AS 出库单号,
    wsof.STATUS AS 出库状态,
    wsof.OUT_TYPE AS 出库类型,
    wsof.DOCKAGE_WEIGHT_OUT_PLAN AS 计划扣杂重量,
    wsof.DOCKAGE_WEIGHT_OUT_FACT AS 实际扣杂重量,
    wsof.WEIGHT_OUT_PLAN AS 计划出库重量,
    wsof.WEIGHT_OUT_FACT AS 实际出库重量,
    wsof.CREATED_TIME AS 创建时间,
    wsof.UPDATED_TIME AS 更新时间
FROM 
    wms_stock_out_form wsof
WHERE 
    wsof.OUT_NO = 'ROA20260304005'
    AND wsof.DELETED = 0;

-- 2. 查询出库单分录信息（按批次）
SELECT 
    '出库单分录信息' AS 查询类型,
    wsop.OUT_NO AS 出库单号,
    wsop.BATCH_NO AS 批次号,
    wsop.MATERIAL_CODE AS 物料编码,
    wsop.DOCKAGE_WEIGHT_OUT_PLAN AS 分录计划扣杂重量,
    wsop.DOCKAGE_WEIGHT_OUT_FACT AS 分录实际扣杂重量,
    wsop.WEIGHT_OUT_PLAN AS 分录计划出库重量,
    wsop.WEIGHT_OUT_FACT AS 分录实际出库重量,
    wsop.GROSS_WEIGHT_OUT_FACT AS 分录毛重,
    wsop.TARE_WEIGHT_OUT_FACT AS 分录皮重
FROM 
    wms_stock_out_product wsop
WHERE 
    wsop.OUT_NO = 'ROA20260304005'
    AND wsop.BATCH_NO = '25252'
    AND wsop.DELETED = 0;

-- 3. 查询出库单明细信息（条码级别）
SELECT 
    '出库单明细信息' AS 查询类型,
    wsopd.OUT_NO AS 出库单号,
    wsopd.BATCH_NO AS 批次号,
    wsopd.BARCODE AS 条码,
    wsopd.SERIAL_NO AS 细码,
    wsopd.GOODS_NO AS 货号,
    wsopd.DOCKAGE_WEIGHT_OUT_FACT AS 明细扣杂重量,
    wsopd.WEIGHT_OUT_FACT AS 明细出库重量,
    wsopd.GROSS_WEIGHT_OUT_FACT AS 明细毛重,
    wsopd.TARE_WEIGHT_OUT_FACT AS 明细皮重,
    wsopd.IS_SPLIT AS 是否拆分,
    wsopd.ORIGINAL_DOCKAGE_WEIGHT AS 原扣杂重量
FROM 
    wms_stock_out_product_detail wsopd
WHERE 
    wsopd.OUT_NO = 'ROA20260304005'
    AND wsopd.BATCH_NO = '25252'
    AND wsopd.DELETED = 0
ORDER BY wsopd.BARCODE, wsopd.SERIAL_NO;

-- 4. 查询对应的库存明细信息（出库前后对比）
SELECT 
    '库存明细信息' AS 查询类型,
    mwsd.BATCH_NO AS 批次号,
    mwsd.BARCODE AS 条码,
    mwsd.SERIAL_NO AS 细码,
    mwsd.GOODS_NO AS 货号,
    mwsd.LEFT_DOCKAGE_WEIGHT AS 剩余扣杂重量,
    mwsd.LEFT_WEIGHT AS 剩余重量,
    mwsd.LEFT_GROSS_WEIGHT AS 剩余毛重,
    mwsd.LEFT_TARE_WEIGHT AS 剩余皮重,
    mwsd.DOCKAGE_WEIGHT AS 初始扣杂重量,
    mwsd.UPDATED_TIME AS 更新时间
FROM 
    material_warehouse_stock_detail mwsd
WHERE 
    mwsd.BATCH_NO = '25252'
    AND mwsd.DELETED = 0
    AND mwsd.LEFT_WEIGHT > 0  -- 还有剩余库存的
ORDER BY mwsd.BARCODE, mwsd.SERIAL_NO;

-- 5. 扣杂重量分配验证查询（关键验证）
SELECT 
    '扣杂分配验证' AS 查询类型,
    wsopd.BATCH_NO AS 批次号,
    wsopd.BARCODE AS 条码,
    wsopd.SERIAL_NO AS 细码,
    wsopd.DOCKAGE_WEIGHT_OUT_FACT AS 出库扣杂重量,
    wsopd.IS_SPLIT AS 是否拆分,
    mwsd.DOCKAGE_WEIGHT AS 库存初始扣杂重量,
    mwsd.LEFT_DOCKAGE_WEIGHT AS 库存剩余扣杂重量,
    -- 计算验证：出库前扣杂重量 = 出库扣杂重量 + 剩余扣杂重量
    (wsopd.DOCKAGE_WEIGHT_OUT_FACT + mwsd.LEFT_DOCKAGE_WEIGHT) AS 计算的初始扣杂重量,
    -- 验证是否匹配
    CASE 
        WHEN ABS(mwsd.DOCKAGE_WEIGHT - (wsopd.DOCKAGE_WEIGHT_OUT_FACT + mwsd.LEFT_DOCKAGE_WEIGHT)) < 0.001 
        THEN '✓ 匹配' 
        ELSE '✗ 不匹配' 
    END AS 扣杂分配验证结果,
    -- 拆分出库扣杂处理验证
    CASE 
        WHEN wsopd.IS_SPLIT = 1 AND wsopd.DOCKAGE_WEIGHT_OUT_FACT = 0 
        THEN '⚠ 拆分出库扣杂为0（可能有问题）'
        WHEN wsopd.IS_SPLIT = 1 AND wsopd.DOCKAGE_WEIGHT_OUT_FACT > 0
        THEN '✓ 拆分出库扣杂按比例分配'
        ELSE '✓ 完整出库'
    END AS 拆分处理验证结果
FROM 
    wms_stock_out_product_detail wsopd
    LEFT JOIN material_warehouse_stock_detail mwsd 
        ON wsopd.BATCH_NO = mwsd.BATCH_NO 
        AND wsopd.BARCODE = mwsd.BARCODE 
        AND wsopd.SERIAL_NO = mwsd.SERIAL_NO
        AND mwsd.DELETED = 0
WHERE 
    wsopd.OUT_NO = 'ROA20260304005'
    AND wsopd.BATCH_NO = '25252'
    AND wsopd.DELETED = 0
ORDER BY wsopd.BARCODE, wsopd.SERIAL_NO;

-- 6. 汇总验证查询
SELECT 
    '汇总验证' AS 查询类型,
    '批次25252' AS 批次号,
    SUM(wsopd.DOCKAGE_WEIGHT_OUT_FACT) AS 明细扣杂重量合计,
    MAX(wsop.DOCKAGE_WEIGHT_OUT_FACT) AS 分录扣杂重量,
    MAX(wsof.DOCKAGE_WEIGHT_OUT_FACT) AS 主表扣杂重量,
    -- 验证三级汇总是否一致
    CASE 
        WHEN ABS(SUM(wsopd.DOCKAGE_WEIGHT_OUT_FACT) - MAX(wsop.DOCKAGE_WEIGHT_OUT_FACT)) < 0.001 
             AND ABS(MAX(wsop.DOCKAGE_WEIGHT_OUT_FACT) - MAX(wsof.DOCKAGE_WEIGHT_OUT_FACT)) < 0.001
        THEN '✓ 三级汇总一致' 
        ELSE '✗ 三级汇总不一致（存在问题）' 
    END AS 汇总一致性验证
FROM 
    wms_stock_out_product_detail wsopd
    LEFT JOIN wms_stock_out_product wsop 
        ON wsopd.OUT_NO = wsop.OUT_NO 
        AND wsopd.BATCH_NO = wsop.BATCH_NO
        AND wsop.DELETED = 0
    LEFT JOIN wms_stock_out_form wsof 
        ON wsopd.OUT_NO = wsof.OUT_NO
        AND wsof.DELETED = 0
WHERE 
    wsopd.OUT_NO = 'ROA20260304005'
    AND wsopd.BATCH_NO = '25252'
    AND wsopd.DELETED = 0;