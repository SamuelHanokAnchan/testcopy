import {PolygonModel} from './polygon-model';

describe('Test Polygon Model', () => {
  it('Testing square and point in shape', () => {
    let square = new PolygonModel([[0, 0], [20, 0], [20, 20], [0, 20]]);
    expect(square.pointIsInArea(5, 15)).toBeTruthy();
  })
  it('Testing hexagon and point in shape', () => {
    let hexagon = new PolygonModel([[6, 0], [14, 0], [20, 10], [14, 20], [6, 20], [0, 10]]);
    expect(hexagon.pointIsInArea(3, 15)).toBeTruthy();
  })
  it('Testing polygon and point in shape', () => {

    let hexagon = new PolygonModel([[394,108],[554,205],[532,273],[377,236]]);
    expect(hexagon.pointIsInArea(497,185)).toBeTruthy();
  })
  it('Testing polygon and point in shape', () => {

    let hexagon = new PolygonModel([[394,108],[554,205],[532,273],[377,236]]);
    expect(hexagon.pointIsInArea(393,211)).toBeTruthy();
  })
  it('Testing polygon and point in shape', () => {

    let hexagon = new PolygonModel([[394,108],[554,205],[532,273],[377,236]]);
    expect(hexagon.pointIsInArea(493,233)).toBeTruthy();
  })
  it('Testing polygon and point not in shape over right corner', () => {

    let hexagon = new PolygonModel([[394,108],[554,205],[532,273],[377,236]]);
    expect(hexagon.pointIsInArea(521,169)).toBeTruthy();
  })
  it('Testing polygon and point not in shape under right corner', () => {

    let hexagon = new PolygonModel([[394,108],[554,205],[532,273],[377,236]]);
    expect(hexagon.pointIsInArea(522,293)).toBeTruthy();
  })
})
