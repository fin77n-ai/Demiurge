const TEMPLATES = [
  {
    id: 'saas',
    name: 'SaaS 产品',
    desc: '订阅制 Web 应用',
    cards: [
      { type: 'flow',       title: '用户注册 / 登录',     desc: '邮箱注册、OAuth 第三方登录、密码找回' },
      { type: 'flow',       title: '订阅 & 支付',          desc: '免费试用 → 升级付费，Stripe 结账' },
      { type: 'feature',    title: '核心功能模块',          desc: '描述你的核心业务功能' },
      { type: 'feature',    title: '用户仪表盘',            desc: '数据概览、最近活动、快捷操作' },
      { type: 'feature',    title: '通知系统',              desc: '邮件 + 站内通知，可配置偏好' },
      { type: 'data',       title: 'User & Subscription',  desc: 'id, email, plan, trialEndsAt, createdAt' },
      { type: 'constraint', title: '多租户隔离',             desc: '每个用户只能访问自己的数据' },
    ],
  },
  {
    id: 'landing',
    name: '落地页',
    desc: '产品营销 + 转化',
    cards: [
      { type: 'ui',         title: 'Hero 区',               desc: '大标题、副标题、主 CTA 按钮、产品截图' },
      { type: 'ui',         title: '功能特性区',             desc: '3–6 个特性，图标 + 简短描述' },
      { type: 'ui',         title: '定价区',                 desc: '2–3 个套餐，推荐套餐高亮' },
      { type: 'ui',         title: '客户评价区',             desc: '头像、姓名、职位、引言' },
      { type: 'ui',         title: 'FAQ 区',                 desc: '可展开的常见问题列表' },
      { type: 'feature',    title: '邮件收集 / 等待列表',    desc: '表单提交 → 存库 → 发确认邮件' },
      { type: 'constraint', title: 'Core Web Vitals',       desc: 'LCP < 2.5s，CLS < 0.1，无 JS 也能渲染' },
    ],
  },
  {
    id: 'mobile',
    name: '移动 App',
    desc: 'iOS / Android',
    cards: [
      { type: 'flow',       title: '引导 & 登录',           desc: 'Onboarding 3 步，手机号 / 社交登录' },
      { type: 'flow',       title: '核心用户旅程',           desc: '描述用户完成主要任务的步骤' },
      { type: 'ui',         title: '底部 Tab 导航',          desc: '首页、发现、消息、我的，最多 5 个' },
      { type: 'feature',    title: '推送通知',               desc: 'FCM / APNs，用户可分类开关' },
      { type: 'feature',    title: '离线支持',               desc: '核心数据本地缓存，断网可读' },
      { type: 'data',       title: '用户 Profile',           desc: 'uid, nickname, avatar, deviceToken' },
      { type: 'constraint', title: '权限最小化',             desc: '仅在需要时请求相机/位置权限' },
    ],
  },
  {
    id: 'admin',
    name: '管理后台',
    desc: '内部运营工具',
    cards: [
      { type: 'feature',    title: '用户管理',               desc: '列表、搜索、封禁、角色分配' },
      { type: 'feature',    title: '数据统计看板',            desc: '关键指标图表，支持日 / 周 / 月筛选' },
      { type: 'feature',    title: '内容审核',               desc: '待审队列、一键通过 / 拒绝、备注' },
      { type: 'feature',    title: '操作日志',               desc: '记录所有管理员操作，不可删除' },
      { type: 'ui',         title: '左侧菜单导航',            desc: '可收起，分组，支持权限显隐' },
      { type: 'data',       title: 'Admin & Role',           desc: 'adminId, role, permissions[], lastLogin' },
      { type: 'constraint', title: 'RBAC 权限控制',          desc: '每个菜单和接口都要鉴权' },
    ],
  },
  {
    id: 'api',
    name: 'API 服务',
    desc: 'REST / GraphQL 后端',
    cards: [
      { type: 'feature',    title: '认证 & 授权',            desc: 'JWT / API Key，Token 刷新，速率限制' },
      { type: 'feature',    title: '核心业务 CRUD',          desc: '描述主要资源的增删改查接口' },
      { type: 'feature',    title: '分页 & 过滤',            desc: 'cursor 分页，支持字段过滤和排序' },
      { type: 'feature',    title: 'Webhook',               desc: '事件推送，签名验证，重试机制' },
      { type: 'data',       title: '主资源数据结构',          desc: '定义核心 Model 字段' },
      { type: 'constraint', title: '幂等性',                 desc: 'POST 接口支持 Idempotency-Key' },
      { type: 'constraint', title: '错误格式统一',           desc: '{ code, message, details } 结构' },
    ],
  },
]

export default function TemplateModal({ onApply, onClose }) {
  return (
    <div style={S.overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={S.modal}>
        <div style={S.header}>
          <span style={S.title}>从模板开始</span>
          <button style={S.closeBtn} onClick={onClose}>✕</button>
        </div>
        <div style={S.grid}>
          {TEMPLATES.map(t => (
            <button key={t.id} style={S.card} onClick={() => { onApply(t.cards); onClose() }}>
              <div style={S.cardName}>{t.name}</div>
              <div style={S.cardDesc}>{t.desc}</div>
              <div style={S.cardCount}>{t.cards.length} 张卡片</div>
            </button>
          ))}
        </div>
        <div style={S.hint}>模板卡片会追加到当前画板，不会覆盖已有内容</div>
      </div>
    </div>
  )
}

const S = {
  overlay:   { position: 'fixed', inset: 0, background: '#00000088', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  modal:     { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, width: 520, padding: 24, boxShadow: '0 20px 60px #00000090', display: 'flex', flexDirection: 'column', gap: 16 },
  header:    { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  title:     { fontSize: 14, fontWeight: 700, color: 'var(--text)' },
  closeBtn:  { background: 'none', border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: 14, padding: '2px 6px' },
  grid:      { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  card:      { background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '12px 14px', cursor: 'pointer', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 4, transition: 'border-color .15s' },
  cardName:  { fontSize: 13, fontWeight: 700, color: 'var(--text)' },
  cardDesc:  { fontSize: 11, color: 'var(--text2)' },
  cardCount: { fontSize: 10, color: 'var(--primary)', marginTop: 4, fontWeight: 600 },
  hint:      { fontSize: 11, color: 'var(--text2)', textAlign: 'center' },
}
