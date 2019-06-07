import { h, render, Fragment, Component } from 'preact'
import { useState, useCallback } from 'preact/hooks'
import { useDrag } from 'preact/hooks'
import { useEventListener, useSwipe } from './hooks'
import { tokenise, TOKENS } from './chordpro'
import { map, copy, scrollToInternal, toggleFullScreen, toggleWakeLock } from './platform'
import { transposeChord, calculateTranspose, NOTES_ALL } from './music'


// the main application component
function SetList ({ setlist }) {
  const [order, setOrder] = useState(setlist.order)
  const setNewOrder = useCallback(o => setOrder(o), [order, setOrder])
  return (
    <Fragment>
      <Index setlist={setlist} order={order} setOrder={setNewOrder}/>
      {order.map((id) => <Song key={id} song={setlist.songs[id]} />) }
    </Fragment>
  )
}

function toggleSetlist(ev) {
  toggleFullScreen()
  toggleWakeLock()
}

function Index({ setlist, order, setOrder }) {
  // this does a crude DOM-based Drag and Drop list reordering
  // there's other way to get info that's also available in dragenter to the song being dragged :(
  let draggedSongId = null

  const dragStart = e => {
    e.target.classList.add('dragging')
    draggedSongId = e.target.getAttribute('data-id')
    e.dataTransfer.effectAllowed = 'move'
  }
  const dragOver = e => {
    if (e.preventDefault) e.preventDefault(); // Necessary. Allows us to drop.
    e.dataTransfer.dropEffect = 'move'
    return false
  }

  const dragEnter = e => {
    if (e.target.closest('.song-index').getAttribute('data-id') !== draggedSongId) {
      e.target.classList.add('over')
    }
  }
  const dragLeave = e => e.target.classList.remove('over')
  const dragEnd = e => e.target.classList.remove('dragging')

  const drop = e => {
    // e.target is the drop target
    if (e.stopPropagation) e.stopPropagation(); // stops the browser from redirecting.

    let node = e.target.closest('.song-index')
    const thisSongId = node.getAttribute('data-id')
    const targetIndex = parseInt(node.getAttribute('data-index'))

    if (draggedSongId === thisSongId) {
      return false
    }

    let newOrder = []
    for (let index = 0; index < order.length; index += 1) {
      const id = order[index]
      if (id === draggedSongId) {
        continue
      }
      newOrder.push(id)
      if (index === targetIndex) {
        newOrder.push(draggedSongId)
      }
    }
    setOrder(newOrder)
    draggedSongId = null
    return false;
  }

  return (
      <article class="index page" id="index">
        <header>{ setlist.title }
          <span class="fullscreen" onclick={toggleSetlist} ontouchstart={toggleSetlist}>⛶</span>
        </header>
        <table class="songlist">
          {order.map((id, index) => {
            const song = setlist.songs[id]
            return (
              <tr>
                <td key={'index-' + id}
                    class="song-index"
                    data-id={id}
                    data-index={index}
                    draggable
                    ondragstart={dragStart}
                    ondragover={dragOver}
                    ondragenter={dragEnter}
                    ondragleave={dragLeave}
                    ondragend={dragEnd}
                    ondrop={drop}
                >
                  <span class="handle">≡</span> <FakeInternalLink text={song.title} target={song.id}/>
                </td>
                <td>{ song.key || '?'}</td>
                <td>{ song.time }</td>
                <td>{ song.tempo }</td>
              </tr>
            )
          })}
        </table>
        <section>
          <p>{ setlist.message }</p>
        </section>
      </article>
  )
}

function FakeInternalLink({text, target}) {
  const go = e => scrollToInternal(target)
  return <span class="link" onclick={go} ontouchstart={go}>{text}</span>
}

function Song ({ song }) {
  const [transposedKey, setTransposedKey] = useState(song.key)
  var transposeMap = null
  if (song.key && transposedKey != song.key) {
    transposeMap = calculateTranspose(song.key, transposedKey)
  }
  return (
      <article class="song page" id={song.id}>
        <SongTitle song={song} transposedKey={transposedKey} setKey={setTransposedKey}/>
        {map(song.sections, (name, section) => <Section name={name} section={section} transposeMap={transposeMap}/>)}
      </article>
  )
}

function SongTitle ({ song, transposedKey, setKey }) {
  let key = transposedKey || song.key || ''
  let nodes = []
  if (song.capo) nodes.push('Capo ' + song.capo)
  if (song.time) nodes.push(song.time)
  if (song.tempo) nodes.push(song.tempo)

  return (
    <header class='title'>{ song['title'] }
      <span class='info'>
        <select class="key" value={key} onChange={ev => setKey(ev.target.value)}>
          {NOTES_ALL.map(n => <option >{n}</option>)}
        </select>
        | { nodes.join(' | ') }
        | <FakeInternalLink text="⌂" target="index"/>
      </span>
    </header>
  )
}

function Section ({ name, section, transposeMap }) {
  const [collapsed, setCollapsed] = useState(false)
  const [chords, setChords] = useState(true)
  const lines = section.split(/\n/)
  const toggleCollapsed = e => {
    e.preventDefault()
    setCollapsed(!collapsed)
  }
  const toggleChords = e => {
    e.preventDefault()
    setChords(!chords)
  }
  const _class = (collapsed ? 'collapsed ' : ' ') + (chords ? ' ' : 'hide-chords')
  return (
    <section className={_class}>
      <header>
        <span class='name toggle' onclick={toggleCollapsed} ontouchstart={toggleCollapsed}>{name}</span>
        <span class='collapse toggle' onclick={toggleCollapsed} ontouchstart={toggleCollapsed}> ⯅</span>
        <span class='expand toggle' onclick={toggleCollapsed} ontouchstart={toggleCollapsed}> ⯆</span>
        &nbsp;<span class='show-chords toggle' onclick={toggleChords} ontouchstart={toggleChords}>A♭</span>
      </header>
      {lines.map((l) => <Line line={l} transposeMap={transposeMap} />)}
    </section>
  )
}


const TOKEN_CLASS = {}
TOKEN_CLASS[TOKENS.CHORD] = 'chord'
TOKEN_CLASS[TOKENS.COMMENT] = 'comment'
TOKEN_CLASS[TOKENS.SPACE] = 'space'
TOKEN_CLASS[TOKENS.HYPHEN] = 'hyphen'

const RAISED_TOKENS = [TOKENS.CHORD, TOKENS.COMMENT]

function Line ({ line, transposeMap }) {
  // split on [chords] or {directives}, removing undefineds
  var nodes = []
  const [line_type, tokens] = tokenise(line)

  for (var i = 0; i < tokens.length; i += 1) {
    const [current, next] = tokens[i]
    var className = TOKEN_CLASS[current.type]

    switch (current.type) {
      case TOKENS.CHORD:
      case TOKENS.COMMENT:
        var wrapperClass = "chordlyric "
        var lyric = ' '
        var value = current.value
        // is the next token not a chord/comment?
        if (next && !RAISED_TOKENS.includes(next.type)) {
          if (next.type === TOKENS.SPACE || next.value[0] === '-' || next.value[1] === '-') {
            wrapperClass += 'spaced-chord'
          }
          // pull the next lyric into this node
          lyric = next.value
          i += 1
        }
        if (transposeMap && current.type === TOKENS.CHORD && value !== '|') {
          value = transposeChord(value, transposeMap)
        }
        if (line_type === 'both') {
          nodes.push(
            <span className={wrapperClass}>
              <span className={className}>{value}</span>
              <span class="lyric">{lyric}</span>
            </span>
          )
        } else {
          nodes.push(
            <span className={className}>{value}</span>
          )
        }
        break

      case TOKENS.HYPHEN:
      case TOKENS.SPACE:
        nodes.push(<span className={className}>{current.value}</span>)
        break

      case TOKENS.LYRIC:
        nodes.push(current.value)
        break

      default:
        console.error("Unknown token type: ", current)
        break;
    }
  }
  return <p className={'line ' + line_type}>{nodes}</p>
}

function SetAlight(original_setlist, element) {
  let setlist = copy(original_setlist)
  console.log(setlist)
  render(<SetList setlist={setlist} />, element)
}

const SETLIST = JSON.parse(document.getElementById('setlist').innerHTML)
const app = document.getElementById('app')

SetAlight(SETLIST, app)
