<script lang="ts">
import { Handle, Position, type NodeProps, NodeResizer, NodeToolbar, useUpdateNodeInternals, useSvelteFlow } from '@xyflow/svelte';
import { deleteMoodboardNode } from "$lib/api";

let { id, data, selected }: NodeProps = $props();

const { deleteElements, updateNode } = useSvelteFlow();
const updateNodeInternals = useUpdateNodeInternals();

let rotation = $state(0);
let isLocked = $state(false);
let nodeEl = $state<HTMLElement>();

$effect(() => {
rotation = (data.rotation as number) || 0;
isLocked = (data.isLocked as boolean) || false;
});

async function handleDelete() {
try {
if (data.moodboardId) {
await deleteMoodboardNode(data.moodboardId as string, id);
}
deleteElements({ nodes: [{ id }] });
} catch (e) {
console.error('Failed to delete node', e);
}
}

function resetRotation() {
rotation = 0;
data.rotation = 0;
updateNodeInternals(id);
}

function toggleLock() {
const newLockedState = !isLocked;
isLocked = newLockedState;
data.isLocked = newLockedState;
updateNode(id, { draggable: !newLockedState });
updateNodeInternals(id);
}

let rotating = false;
let ringCursor = $state("crosshair");

function onRotateRingMove(ev: MouseEvent) {
	if (!nodeEl || isLocked || rotating) return;
	const rect = nodeEl.getBoundingClientRect();
	const centerX = rect.left + rect.width / 2;
	const centerY = rect.top + rect.height / 2;
	const dx = ev.clientX - centerX;
	const dy = ev.clientY - centerY;
	let angle = (Math.atan2(dy, dx) * 180) / Math.PI;
	angle += 90;
	
	const svgCursor = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(1px 1px 1px rgba(255,255,255,0.8));"><g transform="rotate(${Math.round(angle)} 12 12)"><path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M3 12a9 9 0 1 1 9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></g></svg>`;
	const encoded = encodeURIComponent(svgCursor).replace(/'/g, "%27").replace(/"/g, "%22");
	ringCursor = `url("data:image/svg+xml;utf8,${encoded}") 12 12, crosshair`;
}

function onRotateStart(e: MouseEvent) {
if (e.button !== 0 || !nodeEl || isLocked) return;
rotating = true;
e.stopPropagation();
e.preventDefault();

const rect = nodeEl.getBoundingClientRect();
const centerX = rect.left + rect.width / 2;
const centerY = rect.top + rect.height / 2;

function onMouseMove(ev: MouseEvent) {
if (!rotating) return;
const dx = ev.clientX - centerX;
const dy = ev.clientY - centerY;
let angle = (Math.atan2(dy, dx) * 180) / Math.PI;
angle += 90;
rotation = Math.round(angle);
if (nodeEl) nodeEl.style.transform = "rotate(${rotation}deg)";
}

function onMouseUp() {
rotating = false;
data.rotation = rotation;
updateNodeInternals(id);
window.removeEventListener('mousemove', onMouseMove);
window.removeEventListener('mouseup', onMouseUp);
}

window.addEventListener('mousemove', onMouseMove);
window.addEventListener('mouseup', onMouseUp);
}
</script>

<NodeToolbar isVisible={selected} position={Position.Bottom} class="rounded-full border border-white/10 bg-surface-card px-2 py-1 flex gap-1 shadow-gestalt mt-6 z-50">
<button
onclick={toggleLock}
class="rounded-full p-2 transition-colors flex items-center justify-center {isLocked ? 'bg-pin-red text-white' : 'text-pin-medium-gray hover:bg-surface-hover hover:text-white'}"
title="Lock Position"
>
{#if isLocked}
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-lock"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
{:else}
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-unlock"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>
{/if}
</button>
{#if rotation !== 0 && !isLocked}
<button
onclick={resetRotation}
class="rounded-full p-2 text-pin-medium-gray hover:bg-pin-red hover:text-white transition-colors flex items-center justify-center font-bold text-[10px]"
title="Reset Rotation"
>
0&deg;
</button>
{/if}
<button
onclick={handleDelete}
class="rounded-full p-2 text-pin-medium-gray hover:bg-pin-red hover:text-white transition-colors flex items-center justify-center"
title="Delete"
>
<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
<path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
</svg>
</button>
</NodeToolbar>

<div
bind:this={nodeEl}
style="transform: rotate({rotation}deg);"
class="image-node group flex items-center justify-center relative rounded-2xl border border-white/10 bg-surface-card shadow-gestalt transition-shadow hover:shadow-gestalt-hover w-full h-full {selected && !isLocked ? 'ring-2 ring-pin-red overflow-visible' : 'overflow-visible'}"
>
{#if selected && !isLocked}
        <!-- Transform rotation dot -->
        <div role="slider" aria-valuenow={rotation} tabindex="0" class="absolute -top-16 left-1/2 -translate-x-1/2 w-16 h-16 flex items-center justify-center cursor-grab active:cursor-grabbing z-50 nodrag" onmousedown={onRotateStart}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="bg-pin-red rounded-full p-[4px] shadow-lg"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </div>
        <!-- Connector line -->
        <div class="absolute -top-14 left-1/2 -translate-x-1/2 w-px h-14 bg-pin-red/50 pointer-events-none -z-10"></div>
{/if}

<NodeResizer isVisible={selected && !isLocked} minWidth={100} minHeight={100} keepAspectRatio={false} handleClass="!w-4 !h-4 !bg-pin-red !border-2 !border-white !rounded-full shadow-md !z-50" />

<div class="w-full h-full rounded-2xl overflow-hidden flex items-center justify-center pointer-events-none">
{#if data?.imageUrl}
        <img
                src={data.imageUrl as string}
                alt={(data.label as string) ?? 'Image'}
                class="w-full h-full object-fill pointer-events-auto"      
                draggable="false"
        />
{:else}
        <div class="flex items-center justify-center bg-surface-hover text-pin-medium-gray w-full h-full pointer-events-auto">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
                </svg>
        </div>
{/if}

{#if data?.label}
<div class="absolute bottom-0 left-0 right-0 border-t border-white/5 bg-surface-card/90 px-3 py-2 text-xs font-medium text-pin-medium-gray backdrop-blur-sm pointer-events-auto">
{data.label}
</div>
{/if}
</div>

<Handle type="target" position={Position.Left} class="!bg-pin-red !border-none !w-0 !h-0 !opacity-0 -z-50 !min-w-0 !min-h-0" />
<Handle type="source" position={Position.Right} class="!bg-pin-red !border-none !w-0 !h-0 !opacity-0 -z-50 !min-w-0 !min-h-0" />
</div>

<style>
.image-node {
min-width: 100px;
min-height: 100px;
}
</style>
