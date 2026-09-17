import { useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

const DAY_WIDTH = 14;
const ROW_HEIGHT = 36;
const HEADER_HEIGHT = 40;

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const BAR_COLORS = [
  { bg: '#ef4444', light: '#fca5a5' },  // red - electrical
  { bg: '#22c55e', light: '#86efac' },  // green - plumbing
  { bg: '#3b82f6', light: '#93c5fd' },  // blue - foundation
  { bg: '#f59e0b', light: '#fcd34d' },  // amber - steel
  { bg: '#8b5cf6', light: '#c4b5fd' },  // purple
  { bg: '#06b6d4', light: '#67e8f9' },  // cyan
];

function parseDate(str) {
  if (!str) return null;
  const d = new Date(str + 'T00:00:00');
  return isNaN(d.getTime()) ? null : d;
}

function formatDate(d) {
  if (!d) return '—';
  return d.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' });
}

function formatMonthLabel(d) {
  return `${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}`;
}

function formatMonthShort(d) {
  return `${MONTH_SHORT[d.getMonth()]} ${d.getFullYear()}`;
}

function startOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function endOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

function buildMonthRanges(taskMin, taskMax) {
  const months = [];
  let cursor = startOfMonth(taskMin);
  const last = endOfMonth(taskMax);

  while (cursor <= last) {
    const monthStart = startOfMonth(cursor);
    const monthEnd = endOfMonth(cursor);
    const rangeStart = monthStart < taskMin ? taskMin : monthStart;
    const rangeEnd = monthEnd > taskMax ? taskMax : monthEnd;
    const daysInRange = daysBetween(rangeStart, rangeEnd) + 1;

    if (daysInRange > 0) {
      months.push({
        key: `${monthStart.getFullYear()}-${monthStart.getMonth()}`,
        label: formatMonthLabel(monthStart),
        shortLabel: formatMonthShort(monthStart),
        start: rangeStart,
        end: rangeEnd,
        monthStart,
        daysInRange,
        width: daysInRange * DAY_WIDTH,
      });
    }

    cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
  }
  return months;
}

function daysBetween(a, b) {
  return Math.round((b - a) / (1000 * 60 * 60 * 24));
}

function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

function flattenWbs(nodes, ganttTasks, depth = 0, result = []) {
  if (!Array.isArray(nodes)) return result;
  nodes.forEach((node, i) => {
    const matched = ganttTasks.find(
      (t) => t.name?.toLowerCase() === node.name?.toLowerCase() || t.wbs_code === node.code
    );
    const hasChildren = Array.isArray(node.children) && node.children.length > 0;
    result.push({
      id: matched?.id ?? node.code ?? `wbs-${depth}-${i}`,
      name: node.name,
      code: node.code,
      depth,
      isSummary: hasChildren,
      start: matched?.start,
      end: matched?.end,
      progress: matched?.progress ?? 0,
      duration_days: node.duration_days ?? matched?.duration_days,
      dependencies: matched?.dependencies ?? [],
    });
    if (hasChildren) flattenWbs(node.children, ganttTasks, depth + 1, result);
  });
  return result;
}

function wbsDepth(code, level) {
  if (level != null) return Math.max(level - 1, 0);
  if (!code) return 0;
  const dots = (String(code).match(/\./g) || []).length;
  if (/^\d+\.0$/.test(String(code))) return Math.max(dots - 1, 0);
  return dots;
}

function buildTaskRows(ganttData, wbsData) {
  const tasks = ganttData?.tasks ?? [];
  if (tasks.some((t) => t.wbs_code)) {
    return tasks.map((t) => ({
      ...t,
      depth: wbsDepth(t.wbs_code, t.level),
      isSummary: t.is_summary ?? false,
      code: t.wbs_code,
    }));
  }
  if (Array.isArray(wbsData) && wbsData.length > 0) {
    const flat = flattenWbs(wbsData, tasks);
    if (flat.length > 0) return flat;
  }
  return tasks.map((t, i) => ({
    ...t,
    depth: 0,
    isSummary: false,
    code: t.wbs_code || String(i + 1),
  }));
}

export default function GanttChart({ ganttData, wbsData, criticalPath = [], criticalPathDays = 0 }) {
  const scrollRef = useRef(null);
  const [collapsed, setCollapsed] = useState({});

  const rows = useMemo(() => buildTaskRows(ganttData, wbsData), [ganttData, wbsData]);
  const criticalPathSet = useMemo(
    () => new Set((criticalPath || []).map((id) => String(id))),
    [criticalPath],
  );
  const isCritical = (row) => row.critical === true || criticalPathSet.has(String(row.id));

  const visibleRows = useMemo(() => {
    const result = [];
    let skipUntilDepth = null;
    for (const row of rows) {
      if (skipUntilDepth !== null) {
        if (row.depth > skipUntilDepth) continue;
        skipUntilDepth = null;
      }
      result.push(row);
      if (row.isSummary && collapsed[row.id]) {
        skipUntilDepth = row.depth;
      }
    }
    return result;
  }, [rows, collapsed]);

  const { timelineStart, days, months } = useMemo(() => {
    const datedRows = visibleRows
      .map((r) => ({ start: parseDate(r.start), end: parseDate(r.end) }))
      .filter((r) => r.start && r.end);

    if (datedRows.length === 0) {
      const start = new Date();
      return { timelineStart: start, days: [], months: [] };
    }

    const taskMin = new Date(Math.min(...datedRows.map((r) => r.start.getTime())));
    const taskMax = new Date(Math.max(...datedRows.map((r) => r.end.getTime())));
    const monthList = buildMonthRanges(taskMin, taskMax);

    if (monthList.length === 0) {
      return { timelineStart: taskMin, days: [], months: [] };
    }

    const rangeStart = monthList[0].start;
    const rangeEnd = monthList[monthList.length - 1].end;
    const totalDays = daysBetween(rangeStart, rangeEnd) + 1;
    const dayList = Array.from({ length: totalDays }, (_, i) => addDays(rangeStart, i));

    return { timelineStart: rangeStart, days: dayList, months: monthList };
  }, [visibleRows]);

  const timelineWidth = days.length * DAY_WIDTH;

  const getBarStyle = (row, colorIdx) => {
    const start = parseDate(row.start);
    const end = parseDate(row.end);
    if (!start || !end || days.length === 0) return null;

    const left = daysBetween(timelineStart, start) * DAY_WIDTH;
    const width = Math.max((daysBetween(start, end) + 1) * DAY_WIDTH - 4, 12);
    const progress = row.progress ?? 0;
    const colors = BAR_COLORS[colorIdx % BAR_COLORS.length];

    if (row.isSummary) {
      return { left, width, colors, progress, isSummary: true };
    }
    if (progress >= 100) {
      return { left, width, colors: { bg: '#14b8a6', light: '#5eead4' }, progress: 100, label: 'Done' };
    }
    if (progress > 0) {
      return { left, width, colors: { bg: '#6366f1', light: '#a5b4fc' }, progress, label: 'In Progress' };
    }
    return { left, width, colors, progress: 0, label: '' };
  };

  const toggleCollapse = (id) => {
    setCollapsed((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const syncScroll = (e) => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = e.target.scrollTop;
    }
  };

  if (visibleRows.length === 0) {
    return <p className="text-gray-500 text-center py-8">No tasks with schedule dates to display.</p>;
  }

  return (
    <div className="gantt-container border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm">
      {/* Toolbar stats */}
      <div className="flex items-center gap-6 px-4 py-2 bg-slate-50 border-b border-gray-200 text-xs text-gray-500 flex-wrap">
        <span><strong className="text-gray-700">{visibleRows.length}</strong> tasks</span>
        <span><strong className="text-gray-700">{ganttData?.total_duration_days ?? '—'}</strong> days total</span>
        {criticalPath.length > 0 && (
          <span><strong className="text-red-600">{criticalPathDays}</strong> critical path days</span>
        )}
        <span className="flex items-center gap-3 ml-auto">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-teal-500" /> Done</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-indigo-500" /> In Progress</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500" /> Scheduled</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm border-2 border-red-500" /> Critical Path</span>
          <span className="flex items-center gap-1"><span className="w-5 h-2 rounded-full border border-dashed border-amber-400 bg-amber-100/60" /> Float</span>
        </span>
      </div>

      <div className="flex" style={{ height: Math.min(visibleRows.length * ROW_HEIGHT + HEADER_HEIGHT + 20, 600) }}>
        {/* Left: Task table */}
        <div className="flex-shrink-0 border-r border-gray-200 z-10 bg-white" style={{ width: 420 }}>
          {/* Table header */}
          <div
            className="grid grid-cols-[32px_1fr_72px_88px_88px] bg-[#2c5282] text-white text-xs font-semibold border-b border-[#1a365d]"
            style={{ height: HEADER_HEIGHT }}
          >
            <div className="flex items-center justify-center border-r border-[#1a365d]/50">#</div>
            <div className="flex items-center px-2 border-r border-[#1a365d]/50">Task Name</div>
            <div className="flex items-center px-2 border-r border-[#1a365d]/50">Duration</div>
            <div className="flex items-center px-2 border-r border-[#1a365d]/50">Start</div>
            <div className="flex items-center px-2">End</div>
          </div>
          {/* Table body - sync scroll */}
          <div
            className="overflow-y-auto overflow-x-hidden gantt-left-scroll"
            style={{ height: `calc(100% - ${HEADER_HEIGHT}px)` }}
            onScroll={syncScroll}
            ref={scrollRef}
          >
            {visibleRows.map((row, idx) => {
              const start = parseDate(row.start);
              const end = parseDate(row.end);
              const duration = row.duration_days ?? (start && end ? daysBetween(start, end) + 1 : '—');
              return (
                <div
                  key={row.id ?? idx}
                  className={`grid grid-cols-[32px_1fr_72px_88px_88px] text-xs border-b border-gray-100 hover:bg-blue-50/50 ${
                    idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'
                  } ${row.isSummary ? 'font-semibold' : ''}`}
                  style={{ height: ROW_HEIGHT }}
                >
                  <div className="flex items-center justify-center text-gray-400 border-r border-gray-100">{idx + 1}</div>
                  <div
                    className="flex items-center gap-1 px-1 border-r border-gray-100 truncate"
                    style={{ paddingLeft: 8 + row.depth * 16 }}
                    title={row.name}
                  >
                    {row.isSummary && (
                      <button
                        onClick={() => toggleCollapse(row.id)}
                        className="p-0.5 hover:bg-gray-200 rounded shrink-0"
                      >
                        {collapsed[row.id] ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>
                    )}
                    <span className="truncate">{row.code && <span className="text-gray-400 mr-1">{row.code}</span>}{row.name}</span>
                  </div>
                  <div className="flex items-center px-2 text-gray-600 border-r border-gray-100">{duration}{typeof duration === 'number' ? 'd' : ''}</div>
                  <div className="flex items-center px-2 text-gray-600 border-r border-gray-100">{formatDate(start)}</div>
                  <div className="flex items-center px-2 text-gray-600">{formatDate(end)}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Timeline */}
        <div className="flex-1 overflow-auto gantt-right-scroll" onScroll={(e) => { if (scrollRef.current) scrollRef.current.scrollTop = e.target.scrollTop; }}>
          <div style={{ width: timelineWidth, minWidth: '100%' }}>
            {/* Timeline header — monthly */}
            <div className="sticky top-0 z-20 bg-[#2c5282] text-white border-b border-[#1a365d]" style={{ height: HEADER_HEIGHT }}>
              <div className="flex h-full">
                {months.map((month) => (
                  <div
                    key={month.key}
                    className="flex flex-col items-center justify-center border-r border-[#1a365d]/50 px-1"
                    style={{ width: month.width, minWidth: month.width }}
                  >
                    <span className="text-[11px] font-semibold leading-tight">{month.shortLabel}</span>
                    <span className="text-[9px] text-blue-200/80">{month.daysInRange} days</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Timeline rows */}
            {visibleRows.map((row, idx) => {
              const bar = getBarStyle(row, idx);
              const critical = isCritical(row);
              return (
                <div
                  key={row.id ?? idx}
                  className={`relative border-b border-gray-100 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'}`}
                  style={{ height: ROW_HEIGHT }}
                >
                  {/* Month grid */}
                  <div className="absolute inset-0 flex">
                    {months.map((month, i) => (
                      <div
                        key={month.key}
                        className={`border-r border-gray-200 ${i % 2 === 0 ? 'bg-transparent' : 'bg-slate-50/40'}`}
                        style={{ width: month.width, minWidth: month.width }}
                      />
                    ))}
                  </div>

                  {/* Task bar */}
                  {bar && (
                    <>
                    <div
                      className={`absolute top-1/2 -translate-y-1/2 rounded-sm overflow-hidden shadow-sm ${
                        critical ? 'ring-2 ring-red-500 ring-offset-1' : ''
                      }`}
                      style={{
                        left: bar.left + 2,
                        width: bar.width,
                        height: row.isSummary ? 14 : 22,
                        marginTop: row.isSummary ? 0 : 0,
                      }}
                      title={`${row.name}: ${bar.progress}%${row.float_days > 0 ? ` (${row.float_days}d float)` : row.critical ? ' (critical)' : ''}`}
                    >
                      {row.isSummary ? (
                        /* Summary bar with bracket style */
                        <div className="relative h-full flex items-center">
                          <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#1e40af]" style={{ borderRadius: '2px 0 0 2px' }} />
                          <div className="flex-1 h-[6px] bg-[#93c5fd] mx-1.5" />
                          <div className="absolute right-0 top-0 bottom-0 w-1.5 bg-[#1e40af]" style={{ borderRadius: '0 2px 2px 0' }} />
                        </div>
                      ) : (
                        /* Task bar with progress */
                        <div className="relative h-full rounded-full" style={{ backgroundColor: bar.colors.light }}>
                          <div
                            className="absolute inset-y-0 left-0 rounded-full flex items-center px-2"
                            style={{
                              width: `${Math.max(bar.progress, bar.progress > 0 ? 15 : 0)}%`,
                              backgroundColor: bar.colors.bg,
                              minWidth: bar.progress > 0 ? 40 : 0,
                            }}
                          >
                            {bar.width > 80 && bar.label && (
                              <span className="text-[9px] font-semibold text-white truncate whitespace-nowrap">
                                {bar.label}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    {!row.isSummary && row.float_days > 0 && bar && (
                      <div
                        className="absolute top-1/2 -translate-y-1/2 rounded-full border border-dashed border-amber-400/70 bg-amber-100/40"
                        style={{
                          left: bar.left + bar.width + 4,
                          width: Math.max(row.float_days * DAY_WIDTH - 4, 8),
                          height: 18,
                        }}
                        title={`${row.float_days} days float`}
                      />
                    )}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
